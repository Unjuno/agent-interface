"""The frozen source gate remains usable from a later delivery commit."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
T3_REL = Path("research/live_control/owner_keyup_keymap_witness_5156_t3_v1")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def run_preflight_with_delivery_commit(changed_dependency: bool = False) -> dict:
    with tempfile.TemporaryDirectory() as temp:
        repo = Path(temp)
        target = repo / T3_REL
        target.parent.mkdir(parents=True)
        shutil.copytree(ROOT / T3_REL, target)

        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Preflight Test")
        git(repo, "config", "user.email", "preflight-test@example.invalid")
        git(repo, "add", str(T3_REL))
        git(repo, "commit", "-qm", "freeze source")
        frozen_commit = git(repo, "rev-parse", "HEAD")

        frozen_files = {}
        for source in sorted((repo / T3_REL).iterdir()):
            if not source.is_file():
                continue
            relpath = source.relative_to(repo).as_posix()
            frozen_files[relpath] = {
                "git_blob": git(repo, "rev-parse", f"{frozen_commit}:{relpath}"),
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }

        if changed_dependency:
            changed_file = target / "EXPECTED.json"
            changed_file.write_bytes(changed_file.read_bytes() + b" ")

        package_rel = Path("research/analysis") / PACKAGE.name
        package = repo / package_rel
        package.mkdir(parents=True)
        shutil.copy2(PACKAGE / "preflight.py", package / "preflight.py")
        shutil.copy2(PACKAGE / "freeze_provenance.py", package / "freeze_provenance.py")
        (package / "FREEZE.json").write_text(
            json.dumps({"main_commit": frozen_commit, "source_files": frozen_files}),
            encoding="utf-8",
        )
        git(repo, "add", str(T3_REL), str(package_rel))
        git(repo, "commit", "-qm", "deliver frozen-source probe")

        completed = subprocess.run(
            [sys.executable, str(package / "preflight.py")],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if not completed.stdout:
            raise AssertionError(completed.stderr)
        return json.loads(completed.stdout)


class RebasedPreflightTests(unittest.TestCase):
    def test_preflight_accepts_later_commit_with_identical_frozen_dependencies(self):
        result = run_preflight_with_delivery_commit()
        self.assertEqual(
            result["status"],
            "PASS_SOURCE_FIXTURE_CONSTRUCTION",
            result.get("problems"),
        )
        self.assertEqual(result["candidate_cli_invocations"], 0)
        self.assertEqual(result["problems"], [])

    def test_preflight_rejects_changed_frozen_dependency_in_later_commit(self):
        result = run_preflight_with_delivery_commit(changed_dependency=True)
        self.assertEqual(result["status"], "STOP_INVALID_CONTROL_OR_PROVENANCE")
        self.assertIn(
            "source identity mismatch: research/live_control/owner_keyup_keymap_witness_5156_t3_v1/EXPECTED.json",
            result["problems"],
        )


if __name__ == "__main__":
    unittest.main()
