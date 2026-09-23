"""Reproduce the offline audit controls; never launch a game or input owner."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from audit import HERE, REPO, R1, expected_sources, verify
from test_audit import EXPECTED_SOURCES, PID, controls, event, executor_fixture, fixture, legacy_pass

BASE = "5432f3aa2374753e7ab206ad5e1f3f093ac0a641"


def git_blob(path):
    return subprocess.check_output(["git", "rev-parse", f"HEAD:{path}"],
                                   cwd=REPO, text=True).strip()


def result():
    comparison = controls()
    rows, sources = executor_fixture()
    emitted = {"legacy_pass": legacy_pass(rows),
               "supplement": verify(rows, sources, PID, EXPECTED_SOURCES)}
    rows, sources = fixture()
    event(rows, "input_admission")["physical_key_measurement"]["adapter_edge"].update(
        status="PRESS_UNCONFIRMED", interval=None)
    incomplete = {"legacy_pass": legacy_pass(rows),
                  "supplement": verify(rows, sources, PID, EXPECTED_SOURCES)}
    source_files = [R1 / name for name in ("SOURCE_FREEZE.json", "evaluate.py", "r0_bridge_snapshot.py")]
    source_files += [REPO / "research/live_control" / name for name in (
        "executor_v12.py", "executor_v11.py", "executor_v5.py", "lease_release_v1.py",
        "lease_cause_v2.py", "lease_cause_v1.py", "lease.py")]
    code_sha = {name: hashlib.sha256((HERE / name).read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                for name in ("audit.py", "test_audit.py", "record_controls.py")}
    passed = (comparison["positive_legacy_pass"] and comparison["positive_supplement"]["passed"] and
              all(r["legacy_pass"] and not r["supplement_pass"] for r in comparison["corruptions"]) and
              emitted["legacy_pass"] and emitted["supplement"]["passed"] and
              not incomplete["legacy_pass"] and not incomplete["supplement"]["passed"])
    return {
        "schema": "map01-admission-offline-controls-v2",
        "decision": "PASS_OFFLINE_ADMISSION_CONTROLS" if passed else "FAIL_OFFLINE_ADMISSION_CONTROLS",
        "construction_base": BASE,
        "code_sha256_lf_normalized": code_sha,
        "dependency_git_blobs": {path.relative_to(REPO).as_posix(): git_blob(path.relative_to(REPO).as_posix())
                                 for path in source_files},
        "frozen_runtime_reported_sources": expected_sources(),
        "comparison": comparison,
        "actual_executor_synthetic_backend": emitted,
        "incomplete_physical_control": incomplete,
        "counts": {"synthetic_integrity_corruptions": len(comparison["corruptions"]),
                   "legacy_accepts_corruptions": sum(r["legacy_pass"] for r in comparison["corruptions"]),
                   "supplement_rejects_corruptions": sum(not r["supplement_pass"] for r in comparison["corruptions"])},
        "scope": "offline controls only; physical edges and sources in fixtures are synthetic",
        "execution_counts_this_supplement_only": {"live_x11_sessions": 0, "map01_sessions": 0,
                                                  "model_calls": 0, "r1_construction_sessions": 0,
                                                  "r1_formal_sessions": 0},
        "full_r1_gate_eligible": False,
        "performance_claims": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--check", type=Path)
    args = parser.parse_args()
    value = result()
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
    elif args.check:
        if json.loads(args.check.read_text(encoding="utf-8")) != value:
            print("FAIL: retained controls or source identities changed")
            return 1
    else:
        print(encoded, end="")
    print(json.dumps({"counts": value["counts"], "result_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                      "retained_match": True if args.check else None,
                      "full_r1_gate_eligible": False}))
    return 0 if value["decision"] == "PASS_OFFLINE_ADMISSION_CONTROLS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
