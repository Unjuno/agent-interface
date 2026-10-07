"""Independent source-provenance and result-predicate audit for A01."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
EXPECTED = {
    "unchanged_fresh": "VALID",
    "changed_target": "MISSING",
    "duplicate_target": "AMBIGUOUS",
    "focus_changed": "SCOPE_MISMATCH",
    "window_translation": "REVALIDATED",
    "local_move": "MOVED",
    "stale_observation": "STALE",
    "missing_alias": "MISSING",
}


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    for relative, record in freeze["sources"].items():
        source = (REPO / relative).read_bytes()
        actual_sha = hashlib.sha256(source).hexdigest()
        actual_blob = subprocess.check_output(
            ["git", "rev-parse", f"{freeze['source_commit']}:{relative}"],
            cwd=REPO, text=True).strip()
        blob_bytes = subprocess.check_output(
            ["git", "show", f"{freeze['source_commit']}:{relative}"], cwd=REPO)
        assert actual_sha == record["worktree_sha256"], relative
        assert actual_blob == record["git_blob"], relative
        assert hashlib.sha256(blob_bytes).hexdigest() == record["git_blob_sha256"], relative
    probe = json.loads((PACKAGE / "PROBE.json").read_text(encoding="utf-8"))
    actual = {name: row["status"] for name, row in probe["case_results"].items()}
    assert actual == EXPECTED, (actual, EXPECTED)
    assert all(not row["eligible"] for name, row in probe["case_results"].items()
               if name != "unchanged_fresh" and name != "window_translation")
    assert probe["case_results"]["unchanged_fresh"]["point"] == [80, 48]
    assert probe["case_results"]["window_translation"]["point"] == [85, 48]
    assert "ordinary admission remains required" in probe["case_results"]["unchanged_fresh"]["authority"]
    assert probe["flat_source_refused_before_registry_insert"]
    assert probe["out_of_bounds_refused"]
    assert probe["input_dispatch_count"] == 0
    runs = json.loads((PACKAGE / "RUNS.json").read_text(encoding="utf-8"))
    assert runs["tests"]["exit_code"] == 0 and runs["pycompile"]["exit_code"] == 0
    test_stderr = (PACKAGE / runs["tests"]["stderr_path"]).read_text(encoding="utf-8")
    assert "Ran 8 tests" in test_stderr and "OK" in test_stderr
    adjacent = runs["adjacent_compiled_suite"]
    if adjacent["exit_code"] != 0:
        adjacent_stderr = (PACKAGE / adjacent["stderr_path"]).read_text(encoding="utf-8")
        assert adjacent["classification"] == "STOP_MISSING_PYTHON_XLIB"
        assert "ModuleNotFoundError: No module named 'Xlib'" in adjacent_stderr
        assert "Ran 29 tests" in adjacent_stderr and "errors=2" in adjacent_stderr
    manifest = (PACKAGE / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    listed = {}
    for row in manifest:
        digest, relative = row.split("  ", 1)
        path = (PACKAGE / relative).resolve()
        assert PACKAGE.resolve() in path.parents and path.is_file(), relative
        assert relative not in listed, relative
        listed[relative] = digest
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative
    actual_paths = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS" and "__pycache__" not in path.parts
    }
    assert set(listed) == actual_paths
    print(json.dumps({"status": "PASS_COORDINATE_GROUNDING_CONSTRUCTION_AUDIT",
                      "frozen_sources": len(freeze["sources"]),
                      "cases": len(actual), "adjacent_suite": adjacent["classification"],
                      "package_members": len(listed),
                      "input_dispatch_count": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
