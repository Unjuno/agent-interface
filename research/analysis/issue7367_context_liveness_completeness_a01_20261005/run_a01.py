import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "research/analysis/issue7367_context_liveness_a01_20261004"
sys.path.insert(0, str(SOURCE))
import run_a01 as candidate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    workload = json.loads((SOURCE / "workload.json").read_text(encoding="utf-8-sig"))
    freeze = json.loads((SOURCE / "PRE-RUN.json").read_text(encoding="utf-8-sig"))

    # Exact A01 candidate inputs retain the declared graph. Only the independent
    # workflow oracle below knows about this intentionally omitted consumer.
    declared = candidate.analyze(workload, freeze)
    truth_uses = [("completed-note", "terminal_receipt")]
    evicted = set(declared["evicted_ids"])
    missed = sorted(ident for ident, _field in truth_uses if ident in evicted)

    # A truthful uncertainty declaration is the candidate's existing abstention
    # path; no workflow or graph bytes are changed for this control.
    unknown = candidate.analyze(
        workload, freeze,
        scope={"graph_complete": False, "dynamic_consumers_possible": True},
    )
    raw = {
        "schema": "issue7367-completeness-boundary-a01-raw-v1",
        "classification": "COMPLETENESS_CONTRACT_GAP_DEMONSTRATED"
        if missed and unknown["disposition"] == "UNKNOWN_KEEP"
        and unknown["evicted_ids"] == [] else "NOT_REPRODUCED",
        "base_main": "0c4be66bcaac697f1019916e3d8ada889abd5ced",
        "a01_inputs": {
            name: sha(SOURCE / name)
            for name in ("PRE-RUN.json", "workload.json", "run_a01.py")
        },
        "declared_candidate": {
            "disposition": declared["disposition"],
            "evicted_ids": declared["evicted_ids"],
            "graph_complete": workload["scope"]["graph_complete"],
            "dynamic_consumers_possible": workload["scope"]["dynamic_consumers_possible"],
        },
        "counterfactual_actual_workflow": {
            "omitted_consumer_node": "hidden_audit",
            "required_uses": [{"record_id": i, "field": f} for i, f in truth_uses],
            "missing_required_records": missed,
        },
        "unknown_scope_control": {
            "disposition": unknown["disposition"],
            "evicted_ids": unknown["evicted_ids"],
        },
        "scope": "deterministic host-side contract probe; explicit counterfactual only",
    }
    Path(args.out).write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(raw, sort_keys=True))


if __name__ == "__main__":
    main()
