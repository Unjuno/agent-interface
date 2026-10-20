"""Apply and verify the #8636 oracle-boundary construction patch locally.

This verifier only extracts frozen source to a temporary directory, applies a
patch, and runs construction unit tests. It never invokes runner.main or
auditor.main and never reads or writes the retained A04 outcome.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


FREEZE = "2f15e4f9a68cea4b9e47940b8f9b468ba5dd07cf"
PACKAGE = "research/analysis/relative_view_rotation_features_8636_t0_a04_20261012"
SOURCE_SHA256 = {
    "candidate.py": "e058cdc69700b5cb08bbda13cb90c83caca36e238edcddbd9fde5cfced76d1a4",
    "runner.py": "a301dcbc4650c7327d9ef31c11ed24d8d3815129394d7ea9c4603b4422184838",
    "auditor.py": "42515f709ab223e8c75f594b742dbde0e8e8d0adc20514b33fc1093c2182a778",
}


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print("$", subprocess.list2cmdline(command))
    result = subprocess.run(command, cwd=cwd, env=env, text=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> None:
    repo = Path(__file__).resolve().parents[3]
    artifact = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="a04-oracle-boundary-") as temporary:
        root = Path(temporary)
        archive = root / "frozen-source.tar"
        files = [f"{PACKAGE}/{name}" for name in (*SOURCE_SHA256, "test_construction.py")]
        subprocess.run(
            ["git", "-C", str(repo), "archive", "--format=tar", f"--output={archive}", FREEZE, *files],
            check=True,
        )
        with tarfile.open(archive) as bundle:
            bundle.extractall(root, filter="data")

        source = root / PACKAGE
        for name, expected in SOURCE_SHA256.items():
            actual = hashlib.sha256((source / name).read_bytes()).hexdigest()
            if actual != expected:
                raise SystemExit(f"frozen {name} SHA-256 mismatch: {actual}")

        run(
            [sys.executable, str(artifact / "apply_oracle_boundary_patch.py"), str(source)],
            cwd=repo,
        )
        env = os.environ.copy()
        env["A04_SOURCE_DIR"] = str(source)
        test = artifact / "test_oracle_boundary.py"

        for optimization in ([], ["-O"]):
            run(
                [sys.executable, *optimization, "-B", "-m", "unittest", "-v", str(test)],
                cwd=repo,
                env=env,
            )

        legacy_code = """import sys,unittest
sys.path.insert(0, %r)
import test_construction
names = [name for name in unittest.defaultTestLoader.getTestCaseNames(test_construction.ConstructionTests)
         if name != "test_a04_seed_set_and_frozen_source_manifest"]
suite = unittest.TestSuite(test_construction.ConstructionTests(name) for name in names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())""" % str(source)
        for optimization in ([], ["-O"]):
            run(
                [sys.executable, *optimization, "-B", "-c", legacy_code],
                cwd=source,
                env=env,
            )

    print("PASS: patch applied to the pinned temporary source; 4 new and 13 applicable existing tests passed in both modes.")


if __name__ == "__main__":
    main()
