"""Run the full offline suite after a genuine guarded bump in a disposable clone."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TRAILER = "Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>"


def run(cwd, *args):
    if Path(cwd).name.endswith(".git") and args[0] == "git":
        args = ("git", "--git-dir", str(cwd), *args[1:])
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def main():
    if run(ROOT, "git", "status", "--porcelain"):
        raise ValueError("Commit migration changes before disposable bumped validation")
    selected = run(ROOT, "git", "rev-parse", "HEAD")
    with tempfile.TemporaryDirectory(prefix=".bumped-validation-", dir=ROOT) as directory:
        fixture = Path(directory)
        local, bare = fixture / "local", fixture / "origin.git"
        run(fixture, "git", "clone", "--no-hardlinks", "--no-tags", "--no-checkout", str(ROOT), str(local))
        run(local, "git", "checkout", "--detach", selected)
        run(fixture, "git", "init", "--bare", str(bare))
        run(local, "git", "remote", "set-url", "origin", str(bare))
        run(local, "git", "config", "user.name", "Offline Bump Validation")
        run(local, "git", "config", "user.email", "test@example.invalid")
        run(local, "git", "config", "push.followTags", "true")
        run(local, "git", "-c", "push.followTags=false", "push", "--no-follow-tags",
            "origin", f"{selected}:refs/heads/selected")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        subprocess.run(
            [sys.executable, ".github/scripts/release.py", "bump", "--sha", selected,
             "--branch", "selected", "--mode", "patch"], cwd=local, env=env, check=True,
        )
        new = run(local, "git", "rev-parse", "HEAD")
        assert new != selected
        assert run(local, "git", "rev-list", "--parents", "-n", "1", new) == f"{new} {selected}"
        assert run(local, "git", "ls-remote", "--refs", "origin", "refs/heads/selected") \
            == f"{new}\trefs/heads/selected"
        assert run(bare, "git", "rev-parse", "refs/heads/selected") == new
        assert run(local, "git", "status", "--porcelain") == ""
        changed = set(run(local, "git", "diff-tree", "--no-commit-id", "--name-only", "-r", new).splitlines())
        assert changed == {
            "Custom Window.xcodeproj/project.pbxproj", "Info.plist", "English.lproj/InfoPlist.strings",
        }
        assert TRAILER in run(local, "git", "log", "-1", "--format=%(trailers:only,unfold)").splitlines()
        assert run(local, "git", "tag", "--list") == ""
        assert run(bare, "git", "tag", "--list") == ""
        subprocess.run(["actionlint"], cwd=local, env=env, check=True)
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", ".github/tests", "-v"],
            cwd=local, env=env, check=True,
        )
        assert run(local, "git", "status", "--porcelain") == ""
        assert run(local, "git", "rev-parse", "HEAD") == new
        assert run(bare, "git", "rev-parse", "refs/heads/selected") == new
        assert run(local, "git", "tag", "--list") == run(bare, "git", "tag", "--list") == ""
        print(f"Verified genuine guarded source-only bump: {selected} -> {new}")
    assert not fixture.exists()
    assert run(ROOT, "git", "status", "--porcelain") == ""
    assert run(ROOT, "git", "rev-parse", "HEAD") == selected
    print("Disposable local/bare-origin fixture removed; live checkout unchanged.")


if __name__ == "__main__":
    main()
