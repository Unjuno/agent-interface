import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "research/analysis/issue7367_context_liveness_a01_20261004"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    raw = json.loads(Path(args.raw).read_text(encoding="utf-8"))
    checks = {
        "base_main_exact": raw["base_main"] == "0c4be66bcaac697f1019916e3d8ada889abd5ced",
        "a01_source_hashes_exact": raw["a01_inputs"] == {
            name: hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()
            for name in ("PRE-RUN.json", "workload.json", "run_a01.py")
        },
        "candidate_accepted_declared_complete_graph": raw["declared_candidate"]["disposition"] == "PROVEN_DEAD_EVICTION",
        "required_hidden_record_evicted": "completed-note" in raw["declared_candidate"]["evicted_ids"],
        "independent_hidden_consumer_needs_evicted_field": raw["counterfactual_actual_workflow"]["required_uses"] == [
            {"record_id": "completed-note", "field": "terminal_receipt"}
        ] and raw["counterfactual_actual_workflow"]["missing_required_records"] == ["completed-note"],
        "unknown_scope_fails_closed": raw["unknown_scope_control"] == {
            "disposition": "UNKNOWN_KEEP", "evicted_ids": []
        },
        "classification_scoped": raw["classification"] == "COMPLETENESS_CONTRACT_GAP_DEMONSTRATED",
    }
    result = {
        "schema": "issue7367-completeness-boundary-a01-audit-v1",
        "passed": all(checks.values()),
        "checks": checks,
        "classification": "PASS_COUNTEREXAMPLE_SCOPED" if all(checks.values()) else "FAIL_AUDIT",
        "limit": "counterfactual completeness assertion only; no real workflow/runtime claim",
    }
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
