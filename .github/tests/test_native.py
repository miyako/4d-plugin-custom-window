"""Execute actual workflow shell blocks with a closed PATH; never native tools."""

import importlib.util
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/release.yml").read_text()
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("native_source", ROOT / ".github/scripts/source_version.py")
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)
PRODUCT = "Custom Window"
BUNDLE = f"test/Plugins/{PRODUCT}.bundle"


def step(name):
    matches = re.findall(
        rf"^      - name: {re.escape(name)}\n"
        r"(?:(?!      - ).*\n)*?        run: \|\n"
        r"((?:          .*(?:\n|$)|[ \t]*\n)+)", WORKFLOW, re.MULTILINE,
    )
    if len(matches) != 1:
        raise AssertionError(f"Expected one actual run block: {name}")
    return textwrap.dedent(matches[0])


STUB = r'''
import json, os, plistlib, sys
from pathlib import Path
tool = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["CALL_LOG"], "a") as log:
    log.write(json.dumps([tool, *args]) + "\n")
product = "Custom Window"
bundle = Path("test/Plugins") / (product + ".bundle")
contents = bundle / "Contents"
mode = os.environ.get("MODE", "")
if tool == "xcodebuild":
    for path in (contents / "MacOS" / product, contents / "Info.plist",
                 contents / "Resources/English.lproj/InfoPlist.strings",
                 contents / "_CodeSignature", Path("build"),
                 bundle.parent / (product + ".build")):
        assert not path.exists(), str(path)
    if mode == "build-fail": sys.exit(70)
    if mode != "missing-binary":
        (contents / "MacOS" / product).write_bytes(b"fresh binary")
    if mode != "missing-plist":
        data = plistlib.loads(Path("Info.plist").read_bytes())
        if mode == "stale-plist": data["CFBundleShortVersionString"] = "0.0.0"
        if mode == "stale-build": data["CFBundleVersion"] = "0.0.0"
        (contents / "Info.plist").write_bytes(plistlib.dumps(data))
    if mode != "missing-localized":
        data = Path("English.lproj/InfoPlist.strings").read_bytes()
        if mode == "stale-localized":
            data = data.replace(os.environ["VERSION"].encode(), b"0.0.0")
        (contents / "Resources/English.lproj/InfoPlist.strings").write_bytes(data)
elif tool == "lipo":
    assert args == ["-info", str(contents / "MacOS" / product)]
    print("Architectures in the fat file: " + os.environ.get("ARCHS", "arm64 x86_64"))
elif tool == "python3":
    assert args == [".github/scripts/source_version.py", "--verify-bundle", str(bundle)]
    os.execv(os.environ["REAL_PYTHON"], [os.environ["REAL_PYTHON"], *args])
elif tool == "base64":
    assert args == ["--decode", "-o", os.environ["RUNNER_TEMP"] + "/certificate.p12"]
    assert sys.stdin.read() == "fixture-certificate"
    if mode == "certificate-decode-fail": sys.exit(78)
    Path(args[-1]).write_bytes(b"fixture certificate, not a credential")
elif tool == "security":
    if args[0] == "find-identity":
        assert args == ["find-identity", "-v", "-p", "codesigning", os.environ["KEYCHAIN_PATH"]]
        if mode != "missing-identity": print('1) FAKE "Developer ID Application: Fixture (TEST)"')
    else:
        keychain = os.environ["RUNNER_TEMP"] + "/build.keychain-db"
        certificate = os.environ["RUNNER_TEMP"] + "/certificate.p12"
        expected = {
            "create-keychain": ["-p", "fixture-keychain", keychain],
            "set-keychain-settings": ["-lut", "21600", keychain],
            "unlock-keychain": ["-p", "fixture-keychain", keychain],
            "import": [certificate, "-P", "fixture-password", "-A", "-t", "cert",
                       "-f", "pkcs12", "-k", keychain],
            "list-keychain": ["-d", "user", "-s", keychain, "login.keychain"],
            "set-key-partition-list": ["-S", "apple-tool:,apple:,codesign:", "-s",
                                      "-k", "fixture-keychain", keychain],
        }
        assert args[1:] == expected[args[0]]
        if mode == args[0] + "-fail": sys.exit(79)
elif tool == "codesign":
    verify = args[0] == "--verify"
    expected = ["--verify", "--deep", "--strict", "--verbose=2", str(bundle)] if verify else [
        "--verbose", "--deep", "--timestamp", "--force", "--options=runtime",
        "--sign", "Developer ID Application: Fixture (TEST)", str(bundle)]
    assert args == expected
    if mode == ("verify-fail" if verify else "sign-fail"): sys.exit(71)
elif tool in ("ditto", "hdiutil"):
    expected = ["-c", "-k", "--keepParent", str(bundle)] if tool == "ditto" else [
        "create", "-format", "UDBZ", "-volname", product, "-srcfolder", str(bundle)]
    assert args[:-1] == expected
    if mode == tool + "-fail": sys.exit(72)
    Path(args[-1]).write_bytes(b"archive")
elif tool == "xcrun":
    if args[:2] == ["notarytool", "store-credentials"]:
        assert args[2:] == ["notarytool-profile", "--apple-id", "fixture-apple-id",
                           "--team-id", "fixture-team", "--password", "fixture-app-password",
                           "--keychain", os.environ["KEYCHAIN_PATH"]]
        if mode == "store-credentials-fail": sys.exit(80)
    elif args[:2] == ["notarytool", "submit"]:
        assert args[3:] == ["--keychain-profile", "notarytool-profile", "--keychain",
                           os.environ["KEYCHAIN_PATH"], "--wait", "--output-format", "json"]
        second = args[2].endswith(".dmg")
        active = not mode.startswith("second-") or second
        scenario = mode.removeprefix("second-") if active else ""
        if scenario == "transport": sys.exit(73)
        if scenario == "accepted-nonzero":
            print('{"status":"Accepted"}'); sys.exit(74)
        if scenario == "malformed": print("bad json")
        elif scenario == "missing-status": print('{"id":"fixture"}')
        else: print(json.dumps({"status": "Invalid" if scenario == "invalid" else "Accepted"}))
    else:
        assert args == ["stapler", "staple", product + "-" + os.environ["VERSION"] + ".dmg"]
        if mode == "staple-fail": sys.exit(75)
elif tool == "plutil":
    assert args == ["-extract", "status", "raw", "-o", "-", "-"]
    try:
        status = json.load(sys.stdin)["status"]
        assert isinstance(status, str)
        print(status)
    except (ValueError, KeyError, AssertionError): sys.exit(76)
else: raise AssertionError(tool)
'''


class NativeShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".native-tests-", dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in (*source.SOURCE_PATHS, Path(".github/scripts/source_version.py"),
                     Path("manifest.json"), Path("constants.xlf")):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        self.version = source.read(self.root)
        self.contents = self.root / BUNDLE / "Contents"
        self.preserved = {}
        for relative in (
            "Windows64/Custom Window.4DX", "QuickLook/Thumbnail.png",
            "Resources/manifest.json", "Resources/constants.xlf",
        ):
            data = (ROOT / BUNDLE / "Contents" / relative).read_bytes()
            self.write(relative, data)
            self.preserved[relative] = data
        for relative in ("MacOS/Dependency.dylib", "Resources/extra.dat",
                         "Frameworks/Dependency.framework/Versions/A/Dependency"):
            self.write(relative, b"dependency")
            self.preserved[relative] = b"dependency"
        (self.contents / "Frameworks/Dependency.framework/Versions/Current").symlink_to("A")
        for relative in ("MacOS/Custom Window", "Info.plist",
                         "Resources/English.lproj/InfoPlist.strings",
                         "_CodeSignature/CodeResources"):
            self.write(relative, b"stale")
        for relative in ("build/stale", "test/Plugins/Custom Window.build/stale",
                         "test/Plugins/Default/Custom Window.bundle/Contents/MacOS/Custom Window"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"stale")
        self.bin = self.root / "closed-path"
        self.bin.mkdir()
        for name in ("xcodebuild", "lipo", "python3", "security", "codesign", "base64",
                     "ditto", "hdiutil", "xcrun", "plutil"):
            path = self.bin / name
            path.write_text(f"#!{sys.executable}\n" + textwrap.dedent(STUB))
            path.chmod(0o755)
        for name in ("rm", "grep", "head", "sed", "cmp"):
            (self.bin / name).symlink_to(shutil.which(name))
        self.log = self.root / "calls.jsonl"
        self.output = self.root / "github-env"
        self.output.touch()
        self.env = {
            "PATH": str(self.bin), "REAL_PYTHON": sys.executable,
            "CALL_LOG": str(self.log), "VERSION": self.version,
            "BUNDLE_PATH": BUNDLE, "KEYCHAIN_PATH": "fixture.keychain",
            "GITHUB_ENV": str(self.output), "PYTHONDONTWRITEBYTECODE": "1",
            "RUNNER_TEMP": str(self.root),
            "CERT_BASE64": "fixture-certificate", "CERT_PASSWORD": "fixture-password",
            "KEYCHAIN_PASSWORD": "fixture-keychain", "APPLE_ID": "fixture-apple-id",
            "TEAM_ID": "fixture-team", "APP_PASSWORD": "fixture-app-password",
        }

    def write(self, relative, data):
        path = self.contents / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def execute(self, name, prefix="", **env):
        script = step(name)
        for key, value in {
            "env.PRODUCT_NAME": PRODUCT, "env.XCODE_PROJECT": PRODUCT + ".xcodeproj",
            "env.MACOS_DEPLOYMENT_TARGET": "10.13",
            "needs.version.outputs.version": self.version,
        }.items():
            script = script.replace("${{ " + key + " }}", value)
        self.assertNotIn("${{", script)
        return subprocess.run(
            ["/bin/bash", "-c", prefix + "\n" + script], cwd=self.root,
            env={**self.env, **env}, text=True, capture_output=True, timeout=30,
        )

    def calls(self, name):
        rows = self.log.read_text().splitlines() if self.log.exists() else []
        return [row[1:] for line in rows if (row := json.loads(line))[0] == name]

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def build(self, **env):
        self.assert_ok(self.execute("build macOS plugin (universal)", **env))

    def test_build_preserves_payload_and_exact_original_native_arguments(self):
        self.build()
        self.assertEqual(self.calls("xcodebuild"), [[
            "-project", PRODUCT + ".xcodeproj", "-target", PRODUCT,
            "-configuration", "Default", "ARCHS=arm64 x86_64", "ONLY_ACTIVE_ARCH=NO",
            "MACOSX_DEPLOYMENT_TARGET=10.13",
            f"CONFIGURATION_BUILD_DIR={self.root}/test/Plugins", "build",
        ]])
        for relative, data in self.preserved.items():
            self.assertEqual((self.contents / relative).read_bytes(), data)
        self.assertTrue((self.contents / "Frameworks/Dependency.framework/Versions/Current").is_symlink())
        self.assert_ok(self.execute("verify universal binary"))
        self.assertEqual(self.output.read_text(), f"BUNDLE_PATH={BUNDLE}\n")

    def test_cleanup_and_build_errors_fail(self):
        result = self.execute("build macOS plugin (universal)", prefix="rm() { return 79; }")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls("xcodebuild"), [])
        self.assertNotEqual(self.execute("build macOS plugin (universal)", MODE="build-fail").returncode, 0)

    def test_missing_and_stale_rebuilt_output_rejected(self):
        for mode in ("missing-binary", "missing-plist", "missing-localized",
                     "stale-plist", "stale-build", "stale-localized"):
            with self.subTest(mode=mode):
                self.build(MODE=mode)
                self.assertNotEqual(self.execute("verify universal binary").returncode, 0)

    def test_exact_architecture_tokens_and_extra_slices_allowed(self):
        self.build()
        for arch in ("arm64", "x86_64", "arm64e x86_64", "arm64 x86_64h",
                     "notarm64 x86_64", "arm64 x86_64_extra"):
            self.assertNotEqual(self.execute("verify universal binary", ARCHS=arch).returncode, 0)
        self.assert_ok(self.execute("verify universal binary", ARCHS="arm64 x86_64 i386"))

    def test_resource_copy_destinations_checked(self):
        self.build()
        for relative in ("Resources/manifest.json", "Resources/constants.xlf"):
            original = (self.contents / relative).read_bytes()
            for value in (None, b"stale"):
                with self.subTest(relative=relative, value=value):
                    if value is None:
                        (self.contents / relative).unlink()
                    else:
                        self.write(relative, value)
                    self.assertNotEqual(self.execute("verify universal binary").returncode, 0)
            self.write(relative, original)

    def test_built_binary_xml_utf16_and_normal_localization(self):
        self.build()
        text = source.text(self.root / source.LOCALIZED)
        fields = dict(re.findall(r'(?m)^(\w+)\s*=\s*"([^"]*)";', text))
        metadata = plistlib.loads((self.contents / "Info.plist").read_bytes())
        for fmt in (plistlib.FMT_XML, plistlib.FMT_BINARY):
            self.write("Info.plist", plistlib.dumps(metadata, fmt=fmt))
            self.write("Resources/English.lproj/InfoPlist.strings", plistlib.dumps(fields, fmt=fmt))
            self.assert_ok(self.execute("verify universal binary"))
        for data in (text.encode(), text.encode("utf-16"),
                     b"\xfe\xff" + text.encode("utf-16-be")):
            self.write("Resources/English.lproj/InfoPlist.strings", data)
            self.assert_ok(self.execute("verify universal binary"))
            self.write("Resources/English.lproj/InfoPlist.strings", text.replace(self.version, "0.0.0").encode("utf-16"))
            self.assertNotEqual(self.execute("verify universal binary").returncode, 0)

    def test_signing_identity_command_and_strict_verify_required(self):
        self.assert_ok(self.execute("codesign"))
        self.assertEqual(len(self.calls("codesign")), 2)
        for mode in ("missing-identity", "sign-fail", "verify-fail"):
            self.assertNotEqual(self.execute("codesign", MODE=mode).returncode, 0)

    def test_certificate_import_and_notary_credentials_actual_shell(self):
        self.assert_ok(self.execute("import Developer ID certificate"))
        self.assertEqual(len(self.calls("security")), 6)
        self.assertEqual(self.output.read_text(),
                         f"KEYCHAIN_PATH={self.root}/build.keychain-db\n")
        self.assert_ok(self.execute("store notarytool credentials"))
        for mode in (
            "certificate-decode-fail", "create-keychain-fail", "set-keychain-settings-fail",
            "unlock-keychain-fail", "import-fail", "list-keychain-fail",
            "set-key-partition-list-fail",
        ):
            self.output.write_text("")
            self.assertNotEqual(self.execute("import Developer ID certificate", MODE=mode).returncode, 0)
            self.assertEqual(self.output.read_text(), "")
        self.assertNotEqual(self.execute("store notarytool credentials",
                                        MODE="store-credentials-fail").returncode, 0)

    def test_both_notary_commands_accepted_and_staple_required(self):
        self.assert_ok(self.execute("package, notarize & staple"))
        self.assertEqual([row[:2] for row in self.calls("xcrun")], [
            ["notarytool", "submit"], ["notarytool", "submit"], ["stapler", "staple"],
        ])
        self.assertEqual(self.output.read_text().splitlines(), [
            f"ZIP_PATH={PRODUCT}-{self.version}.zip", f"DMG_PATH={PRODUCT}-{self.version}.dmg",
        ])

    def test_every_notary_package_and_staple_failure_blocks_publication(self):
        for mode in (
            "transport", "accepted-nonzero", "invalid", "malformed", "missing-status",
            "second-transport", "second-accepted-nonzero", "second-invalid",
            "second-malformed", "second-missing-status",
            "ditto-fail", "hdiutil-fail", "staple-fail",
        ):
            with self.subTest(mode=mode):
                self.output.write_text("")
                self.log.unlink(missing_ok=True)
                self.assertNotEqual(self.execute("package, notarize & staple", MODE=mode).returncode, 0)
                self.assertEqual(self.output.read_text(), "")
                if mode != "staple-fail":
                    self.assertFalse(any(row[:2] == ["stapler", "staple"] for row in self.calls("xcrun")))


if __name__ == "__main__":
    unittest.main()
