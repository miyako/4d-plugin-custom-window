"""Original contract evidence; assertions remain valid after genuine source bumps."""

import importlib.util
from pathlib import Path
import re
import stat
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASE = "f5cae143ce5fe4fd1f821480155dae4cf0a978a0"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("contract_source", ROOT / ".github/scripts/source_version.py")
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)


def original(path, revision=BASE):
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{revision}:{path}"])


class RepositoryContractTests(unittest.TestCase):
    def test_latest_coordinated_header_supersedes_marketing_only_ancestor(self):
        older = original(".github/workflows/bump-version.yml", "4ccb3db").decode()
        self.assertIn("# Bumps MARKETING_VERSION", older)
        latest = original(".github/workflows/bump-version.yml").decode()
        header, body = latest.split("name: Bump version", 1)
        self.assertIn("MARKETING_VERSION/CURRENT_PROJECT_VERSION AND Info.plist", header)
        self.assertIn("CFBundleShortVersionString/CFBundleVersion", header)
        self.assertIn('KEY="MARKETING_VERSION"', body)
        self.assertIn('KEY="CURRENT_PROJECT_VERSION"', body)
        release = original(".github/workflows/release.yml").decode()
        self.assertIn("  push:\n    tags:\n      - 'v*.*.*'", release)
        self.assertNotIn("pull_request:", release)
        self.assertNotIn("branches:", release)
        self.assertNotIn("build-windows:", release)

    def test_source_only_authorized_tokens_and_absent_optional_key(self):
        current = source.read(ROOT)
        for path in source.SOURCE_PATHS:
            with self.subTest(path=path):
                before = original(path)
                if path == source.PROJECT:
                    expected = before.replace(
                        b"MARKETING_VERSION = 2.1.5;",
                        f"MARKETING_VERSION = {current};".encode(),
                    ).replace(
                        b"CURRENT_PROJECT_VERSION = 2.1.1;",
                        f"CURRENT_PROJECT_VERSION = {current};".encode(),
                    )
                elif path == source.LOCALIZED:
                    expected = before.replace(b"2.1.0", current.encode())
                    self.assertIn(b"\r", before)
                    self.assertNotIn(b"\n", before)
                else:
                    expected = before.replace(b"2.1.5", current.encode())
                self.assertEqual((ROOT / path).read_bytes(), expected)
                self.assertEqual(stat.S_IMODE((ROOT / path).stat().st_mode), 0o644)
        self.assertNotIn(b"<key>CFBundleVersion</key>", (ROOT / source.PLIST).read_bytes())

    def test_all_unrelated_original_files_preserved(self):
        paths = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", BASE], text=True,
        ).splitlines()
        allowed = {*map(str, source.SOURCE_PATHS), "README.md",
                   ".github/workflows/bump-version.yml", ".github/workflows/release.yml"}
        for name in paths:
            if name not in allowed:
                with self.subTest(path=name):
                    self.assertEqual((ROOT / name).read_bytes(), original(name))

    def test_native_topology_resources_secret_names_and_deployment_preserved(self):
        before = original(".github/workflows/release.yml").decode()
        after = (ROOT / ".github/workflows/release.yml").read_text()

        def block(workflow, name):
            return workflow.split(f"      - name: {name}\n", 1)[1].split("\n      - name:", 1)[0].rstrip()

        for name in ("import Developer ID certificate", "store notarytool credentials"):
            self.assertEqual(block(before, name), block(after, name))
        secrets = r"\$\{\{ secrets\.([A-Z_]+) \}\}"
        self.assertEqual(re.findall(secrets, before), re.findall(secrets, after))
        for required in (
            "-configuration Default", 'ARCHS="arm64 x86_64"', "ONLY_ACTIVE_ARCH=NO",
            "MACOS_DEPLOYMENT_TARGET: '10.13'",
            'codesign --verify --deep --strict --verbose=2 "$BUNDLE_PATH"',
            'ditto -c -k --keepParent "$BUNDLE_PATH" "$ZIP_PATH"',
            'hdiutil create -format UDBZ -volname "${{ env.PRODUCT_NAME }}" -srcfolder "$BUNDLE_PATH" "$DMG_PATH"',
            'xcrun stapler staple "$DMG_PATH"',
        ):
            self.assertIn(required, before)
            self.assertIn(required, after)
        self.assertEqual(re.findall(r"^  ([a-z-]+):\n(?:(?:    name:|    needs:).*\n)*    runs-on:", after, re.MULTILINE),
                         ["version", "build-macos"])
        self.assertNotIn("windows-latest", after)
        self.assertNotIn("CODE_SIGNING_ALLOWED", after)
        project = (ROOT / source.PROJECT).read_text()
        for required in ("Cocoa.framework in Frameworks", "InfoPlist.strings in Resources",
                         "constants.xlf in CopyFiles", "manifest.json in CopyFiles",
                         "dstSubfolderSpec = 7;", 'SYMROOT = "$(SRCROOT)/test/Plugins";'):
            self.assertIn(required, project)


if __name__ == "__main__":
    unittest.main()
