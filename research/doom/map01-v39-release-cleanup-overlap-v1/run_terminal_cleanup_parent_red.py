"""Reproduce the terminal-flush regression against the frozen #7395 parent."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PARENT = "b17d492aee852e7eff114fb0f4a7d3dcb0531ee7"
PARENT_PATH = "research/doom/doom_typed_release_backend_v3.py"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def main():
    sys.path.insert(0, str(REPO / "research/doom"))
    import test_doom_typed_release_backend_v3 as tests

    source = subprocess.run(
        ["git", "show", f"{PARENT}:{PARENT_PATH}"], cwd=REPO,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout
    test_path = REPO / "research/doom/test_doom_typed_release_backend_v3.py"
    expected_parent_sha = "5478a4bde87f59db545818e30f31f0afb4934bb5851e441eebf8136b49639a0e"
    expected_test_sha = "1cba55ec4b37fd697baaabc8690935004ec88bf30c640f1c8e124225294eba5d"
    if sha256_bytes(source) != expected_parent_sha:
        raise RuntimeError("frozen parent source hash mismatch")
    test_sha = hashlib.sha256(test_path.read_bytes()).hexdigest()
    if test_sha != expected_test_sha:
        raise RuntimeError("candidate regression test source hash mismatch")

    namespace = {"__name__": "frozen_parent_backend"}
    exec(compile(source, PARENT_PATH, "exec"), namespace)
    tests.mod.Backend = namespace["Backend"]
    suite = unittest.TestSuite([
        tests.Tests("test_final_release_all_flushes_buffered_program_rows")
    ])
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    raw = stream.getvalue()
    expected_red = (
        len(result.failures) == 1
        and len(result.errors) == 0
        and "Lists differ: [] != ['a']" in raw
    )
    raw_path = HERE / "RAW_PARENT_TERMINAL_RED.txt"
    raw_path.write_text(raw, encoding="utf-8")
    receipt = {
        "schema": "terminal-cleanup-parent-red-v1",
        "parent_commit": PARENT,
        "parent_source_path": PARENT_PATH,
        "parent_source_sha256": sha256_bytes(source),
        "candidate_test_sha256": test_sha,
        "test_name": "test_final_release_all_flushes_buffered_program_rows",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "observed_expected_failure": expected_red,
        "raw_file": raw_path.name,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }
    (HERE / "PARENT_RED.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(raw, end="")
    print(f"EXPECTED_PARENT_RED={expected_red}")
    return 0 if expected_red else 1


if __name__ == "__main__":
    raise SystemExit(main())
