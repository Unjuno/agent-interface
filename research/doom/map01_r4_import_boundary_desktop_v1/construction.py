#!/usr/bin/env python3
"""Construction-only checks for the frozen source-only audit classifier."""
import hashlib
import json
import os
from pathlib import Path

from analyzer import classify

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


def main():
    out = Path(os.environ["OUT"])
    if not out.is_dir() or any(out.iterdir()):
        raise SystemExit("STOP_CONSTRUCTION_OUTPUT_NOT_FRESH")
    if os.environ.get("EXPECTED_MAIN") != BASE_COMMIT:
        raise SystemExit("STOP_CONSTRUCTION_BASE_MISMATCH")
    if os.environ.get("IMAGE_ID") != IMAGE_ID:
        raise SystemExit("STOP_CONSTRUCTION_IMAGE_MISMATCH")
    source_root = Path("/source")
    source_hashes = {FILES[key]: sha((source_root / path).read_bytes())
                     for key, path in FILES.items()}
    expected_hashes = {FILES[key]: os.environ.get("EXPECTED_" + key.upper(), "")
                       for key in FILES}
    if source_hashes != expected_hashes:
        raise SystemExit("STOP_CONSTRUCTION_SOURCE_HASH_MISMATCH")
    tests = {
        "deferred": ("def f():\n    main()\n", 0, 0),
        "guarded": ("if __name__ == '__main__':\n    main()\n", 0, 1),
        "direct": ("main()\n", 1, 0),
        "conditional": ("if True:\n    main()\n", 1, 0),
        "decorator": ("@build()\ndef f():\n    pass\n", 1, 0),
        "default": ("def f(arg=build()):\n    pass\n", 1, 0),
        "class_body": ("class C:\n    main()\n", 1, 0),
        "lambda_body": ("f = lambda: main()\n", 0, 0),
    }
    rows = []
    for name, (source, module_count, guard_count) in tests.items():
        result = classify(source, "<" + name + ">")
        passed = (len(result["module_calls"]) == module_count
                  and len(result["main_guard_calls"]) == guard_count)
        rows.append({"name": name, "module_call_count": len(result["module_calls"]),
                     "main_guard_call_count": len(result["main_guard_calls"]),
                     "expected_module_call_count": module_count,
                     "expected_main_guard_call_count": guard_count,
                     "pass": passed})
        if not passed:
            raise SystemExit("FAIL_CONSTRUCTION_CONTROL:" + name)
    target_bytes = (source_root / TARGET).read_bytes()
    target = classify(target_bytes.decode("utf-8"), TARGET)
    launch = [row for row in target["module_calls"]
              if row["name"] == "session_map01_v13.main"]
    if not launch:
        raise SystemExit("FAIL_CONSTRUCTION_TARGET_LAUNCH_NOT_FOUND")
    result = {"schema": "issue-3903/import-boundary-construction-v1",
              "base_commit": BASE_COMMIT, "image_id": IMAGE_ID,
              "target_sha256": sha(target_bytes), "controls": rows,
              "target_unguarded_module_launches": launch,
              "source_hashes": source_hashes,
              "target_imported": False, "target_executed": False,
              "game_started": False, "model_calls": 0, "input_events": 0,
              "disposition": "CONSTRUCTION_PASS_ONLY"}
    data = json.dumps(result, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (out / "CONSTRUCTION.json").write_bytes(data)
    print(json.dumps({"disposition": result["disposition"],
                      "controls_passed": len(rows),
                      "target_launches": len(launch),
                      "construction_sha256": sha(data)}, sort_keys=True))


if __name__ == "__main__":
    main()
