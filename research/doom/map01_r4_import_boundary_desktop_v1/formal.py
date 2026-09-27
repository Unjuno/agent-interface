#!/usr/bin/env python3
"""One deterministic AST-only audit; never loads the target Python module."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from analyzer import call_name, classify

BASE_COMMIT = "8652f6a3527d55610185d1103b87d5d9fd8fa985"
IMAGE_ID = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
TARGET = "research/doom/map01_v12_physical_occupancy_live_r1_v1/session_entry.py"
GATE = "research/doom/map01_r4_sparse_checkout_successor_2174/import_gate.py"
FILES = {"target": TARGET, "gate": GATE,
         "analyzer": "research/doom/map01_r4_import_boundary_desktop_v1/analyzer.py",
         "formal": "research/doom/map01_r4_import_boundary_desktop_v1/formal.py",
         "verifier": "research/doom/map01_r4_import_boundary_desktop_v1/verify.py",
         "construction": "research/doom/map01_r4_import_boundary_desktop_v1/construction.py"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(source, expected_module, expected_guard=()):
    got = classify(source)
    module = [row["name"] for row in got["module_calls"]]
    guarded = [row["name"] for row in got["main_guard_calls"]]
    assert module == list(expected_module), (module, expected_module)
    assert guarded == list(expected_guard), (guarded, expected_guard)
    return got


def main():
    source_root = Path("/source")
    out = Path(os.environ["OUT"])
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_FRESH_EMPTY")
    if os.environ.get("EXPECTED_MAIN", "") != BASE_COMMIT:
        raise SystemExit("STOP_BASE_COMMIT_MISMATCH")
    image = os.environ.get("IMAGE_ID", "")
    if image != IMAGE_ID:
        raise SystemExit("STOP_IMAGE_ID_MISMATCH")
    source_data = {key: (source_root / path).read_bytes()
                   for key, path in FILES.items()}
    source_hashes = {FILES[key]: sha(data) for key, data in source_data.items()}
    expected_hashes = {FILES[key]: os.environ.get("EXPECTED_" + key.upper(), "")
                       for key in FILES}
    if source_hashes != expected_hashes:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")

    controls = [
        ("deferred_function", "def f():\n    main()\n", (), ()),
        ("main_guard", "if __name__ == '__main__':\n    main()\n", (), ("main",)),
        ("unguarded_call", "main()\n", ("main",), ()),
        ("conditional_call", "if True:\n    main()\n", ("main",), ()),
        ("decorator_call", "@build()\ndef f():\n    pass\n", ("build",), ()),
        ("default_call", "def f(arg=build()):\n    pass\n", ("build",), ()),
        ("class_body_call", "class C:\n    main()\n", ("main",), ()),
        ("lambda_body_deferred", "f = lambda: main()\n", (), ()),
    ]
    control_results = []
    for name, source, module_expected, guard_expected in controls:
        classified = check(source, module_expected, guard_expected)
        legacy_flags_main = any(
            isinstance(node, ast.Call) and call_name(node.func).split(".")[-1] == "main"
            for node in ast.walk(ast.parse(source)))
        control_results.append({"name": name, "expected": True,
                                "source": source,
                                "expected_module_names": list(module_expected),
                                "expected_main_guard_names": list(guard_expected),
                                "legacy_whole_tree_flags_main": legacy_flags_main,
                                "module_calls": classified["module_calls"],
                                "main_guard_calls": classified["main_guard_calls"]})

    target_class = classify(source_data["target"].decode("utf-8"), TARGET)
    launch = [row for row in target_class["module_calls"]
              if row["name"] == "session_map01_v13.main"]
    assert launch, "UNGUARDED_ARCHIVAL_LAUNCH_NOT_FOUND"
    gate_tree_calls = [row["name"] for row in classify(
        source_data["gate"].decode("utf-8"), GATE)["module_calls"]]
    assert gate_tree_calls, "GATE_HAS_NO_TOP_LEVEL_CALLS"

    formal = {"schema": "issue-3857/import-boundary-formal-v1",
              "issue": 3903,
              "allocation": "issue-3896-dockerdesktop-import-boundary-audit-01",
              "base_commit": BASE_COMMIT, "image_id": image,
              "source_hashes": source_hashes,
              "execution_endpoints": {"target_import": 0, "target_execution": 0,
                                       "game": 0, "model": 0, "input": 0},
              "controls_passed": len(control_results),
              "controls_expected": len(controls),
              "controls": control_results,
              "target_module_calls": target_class["module_calls"],
              "target_main_guard_calls": target_class["main_guard_calls"],
              "target_launch_classification": "UNGUARDED_MODULE_EXECUTION",
              "original_gate_module_calls": gate_tree_calls,
              "disposition": "PASS_STATIC_IMPORT_BOUNDARY_SCOPED"}
    data = json.dumps(formal, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (out / "formal_result.json").write_bytes(data)

    verify = subprocess.run([sys.executable, "/source/research/doom/"
                             "map01_r4_import_boundary_desktop_v1/verify.py",
                             str(out / "formal_result.json"), str(out / "independent_audit.json")],
                            text=True, capture_output=True, check=False, timeout=20)
    (out / "verifier_stdout.txt").write_text(verify.stdout, encoding="utf-8")
    (out / "verifier_stderr.txt").write_text(verify.stderr, encoding="utf-8")
    decision = "PASS_STATIC_IMPORT_BOUNDARY_SCOPED" if verify.returncode == 0 else "FAIL_CLASSIFIER"
    result = {"schema": "issue-3857/import-boundary-result-v1",
              "decision": decision, "formal_result_sha256": sha(data),
              "independent_audit_sha256": sha((out / "independent_audit.json").read_bytes())
              if (out / "independent_audit.json").is_file() else None,
              "verifier_exit_code": verify.returncode,
              "source_hashes": source_hashes,
              "execution_endpoints": formal["execution_endpoints"]}
    result_data = json.dumps(result, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (out / "RESULT.json").write_bytes(result_data)
    print(json.dumps({"decision": decision, "controls": len(control_results),
                      "verifier_exit_code": verify.returncode,
                      "result_sha256": sha(result_data)}, sort_keys=True))
    if decision != "PASS_STATIC_IMPORT_BOUNDARY_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
