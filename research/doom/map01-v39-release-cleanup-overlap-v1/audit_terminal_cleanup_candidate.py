"""Independently audit retained terminal-cleanup candidate run receipts."""
import hashlib
import json
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXPECTED = {"backend": 27, "owner": 8, "wait": 7}
MANIFEST = HERE / "SHA256SUMS.txt"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_rows = MANIFEST.read_text(encoding="utf-8").splitlines()
    assert manifest_rows
    for line in manifest_rows:
        digest, relpath = line.split("  ", 1)
        assert sha256(REPO / relpath) == digest
    receipt = json.loads((HERE / "CANDIDATE_RUN.json").read_text(encoding="utf-8"))
    assert receipt.get("schema") == "terminal-cleanup-candidate-run-v1"
    assert receipt.get("source_sha256") == {
        "backend": sha256(REPO / "research/doom/doom_typed_release_backend_v3.py"),
        "backend_tests": sha256(REPO / "research/doom/test_doom_typed_release_backend_v3.py"),
    }
    runs = receipt.get("runs")
    assert isinstance(runs, list) and len(runs) == len(EXPECTED)
    seen = set()
    for row in runs:
        name = row.get("name")
        assert name in EXPECTED and name not in seen
        seen.add(name)
        raw = HERE / row["raw_file"]
        output = raw.read_text(encoding="utf-8")
        count = EXPECTED[name]
        assert row.get("expected_tests") == count
        assert row.get("returncode") == 0
        assert row.get("raw_sha256") == sha256(raw)
        assert row.get("audited_candidate_pass") is True
        assert re.search(rf"Ran {count} tests in [0-9.]+s", output)
        assert "\nOK\n" in output and "FAILED" not in output
    assert seen == set(EXPECTED)
    parent = json.loads((HERE / "PARENT_RED.json").read_text(encoding="utf-8"))
    parent_raw = HERE / parent["raw_file"]
    parent_output = parent_raw.read_text(encoding="utf-8")
    assert parent.get("schema") == "terminal-cleanup-parent-red-v1"
    assert parent.get("parent_commit") == "b17d492aee852e7eff114fb0f4a7d3dcb0531ee7"
    assert parent.get("parent_source_sha256") == "5478a4bde87f59db545818e30f31f0afb4934bb5851e441eebf8136b49639a0e"
    assert parent.get("candidate_test_sha256") == sha256(REPO / "research/doom/test_doom_typed_release_backend_v3.py")
    assert parent.get("test_name") == "test_final_release_all_flushes_buffered_program_rows"
    assert parent.get("tests_run") == 1 and parent.get("failures") == 1 and parent.get("errors") == 0
    assert parent.get("observed_expected_failure") is True
    assert parent.get("raw_sha256") == sha256(parent_raw)
    assert "Lists differ: [] != ['a']" in parent_output
    print(f"PASS: {len(seen)} retained candidate suite receipts ({sum(EXPECTED.values())} tests), parent RED, {len(manifest_rows)} package hashes match")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
