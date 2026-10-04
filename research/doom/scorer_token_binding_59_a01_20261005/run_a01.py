from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "research/doom/scorer_eventlog_join_t0_v1"
sys.path.insert(0, str(PARENT))
from candidate import classify_intent as classify_v1  # noqa: E402

from candidate_v2 import classify_intent as classify_v2  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    freeze = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
    pinned = freeze["source_sha256"]
    tracked = {
        "parent_candidate.py": PARENT / "candidate.py",
        "parent_file_join.py": PARENT / "file_join.py",
        "candidate_v2.py": PKG / "candidate_v2.py",
        "cases.json": PKG / "cases.json",
        "run_a01.py": PKG / "run_a01.py",
        "audit_a01.py": PKG / "audit_a01.py",
        "README.md": PKG / "README.md",
        "COMMANDS.txt": PKG / "COMMANDS.txt",
        "ENVIRONMENT_STOP.txt": PKG / "ENVIRONMENT_STOP.txt",
    }
    actual_hashes = {name: sha256(path) for name, path in tracked.items()}
    if actual_hashes != pinned:
        raise SystemExit("STOP_FROZEN_SOURCE_HASH_MISMATCH")

    cases = json.loads((PKG / "cases.json").read_text(encoding="utf-8"))
    events = cases["events"]
    samples = cases["samples"]
    intent_id = cases["intent_id"]
    max_gap_ns = cases["max_gap_ns"]
    started_ns = time.perf_counter_ns()
    result = {
        "schema": "scorer-intent-token-binding-a01-v1",
        "allocation_id": "SCORER-INTENT-TOKEN-BINDING-59-A01-20261005-01",
        "source_head": "a2f85482c6968f9caa9dcbca017bd452b8a2c3b3",
        "frozen_runner_invocations": 1,
        "baseline_evaluations": 1,
        "successor_evaluations": 3,
        "retries": 0,
        "execution_environment": {
            "runtime": sys.version,
            "platform": sys.platform,
            "python_executable": sys.executable,
            "containerized": False,
            "container_stop": "Docker image inspection failed on missing containerd content blob; no container was started.",
        },
        "source_sha256": actual_hashes,
        "input_sha256": hashlib.sha256(json.dumps(cases, sort_keys=True,
                                                   separators=(",", ":")).encode()).hexdigest(),
        "started_monotonic_ns": started_ns,
        "cases": {
            "baseline_mismatched_token": classify_v1(
                events["mismatched_token"], samples, intent_id, max_gap_ns=max_gap_ns),
            "candidate_matched_token": classify_v2(
                events["matched_token"], samples, intent_id, max_gap_ns=max_gap_ns),
            "candidate_mismatched_token": classify_v2(
                events["mismatched_token"], samples, intent_id, max_gap_ns=max_gap_ns),
            "candidate_missing_admission_token": classify_v2(
                events["missing_admission_token"], samples, intent_id,
                max_gap_ns=max_gap_ns),
        },
    }
    result["finished_monotonic_ns"] = time.perf_counter_ns()
    observed = result["cases"]
    expected = cases["expected"]
    baseline_reproduced = observed["baseline_mismatched_token"].get("decision") == expected["baseline_mismatched_token"]
    positive_preserved = observed["candidate_matched_token"].get("decision") == expected["candidate_matched_token"]
    mismatch_rejected = (observed["candidate_mismatched_token"].get("decision") == expected["candidate_mismatched_token"]
                         and observed["candidate_mismatched_token"].get("reason") == "intent_token_mismatch")
    missing_rejected = (observed["candidate_missing_admission_token"].get("decision") == expected["candidate_missing_admission_token"]
                        and observed["candidate_missing_admission_token"].get("reason") == "missing_input_intent_token")
    result["gate_checks"] = {
        "baseline_false_accept_reproduced": baseline_reproduced,
        "matched_token_positive_preserved": positive_preserved,
        "mismatched_token_rejected": mismatch_rejected,
        "missing_token_rejected": missing_rejected,
    }
    result["disposition"] = ("PASS_TOKEN_BINDING_SCOPED" if all(result["gate_checks"].values())
                             else "FAIL_TOKEN_BINDING_GATE")
    out = PKG / "results/a01/raw.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "gate_checks": result["gate_checks"],
                      "cases": result["cases"], "source_sha256": result["source_sha256"]},
                     indent=2, sort_keys=True))
    return 0 if result["disposition"] == "PASS_TOKEN_BINDING_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
