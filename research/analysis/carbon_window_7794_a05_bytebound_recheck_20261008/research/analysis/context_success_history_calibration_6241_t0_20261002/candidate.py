"""Deterministic no-model candidate for #6241's success-history T0."""
import argparse
import json
from pathlib import Path


def build(data):
    current = data["current_b"]
    prior = data["prior"]
    threshold = data["proposal_threshold"]
    rows = []
    for case in data["cases"]:
        history = case["history"]
        linked = (
            history["artifact_scope"] == "declared_shared_predictive"
            and history["dependency"] == "same_latent_regime"
            and history["artifact_state"] == "completed"
            and history["capability_id"] == current["capability_id"]
            and history["route_precondition_sha256"] == current["route_precondition_sha256"]
        )
        if history["dependency"] == "unknown":
            status = "HOLD_UNKNOWN_DEPENDENCY"
            transferable = False
        elif case["effect_state"] == "ambiguous":
            status = "HOLD_AMBIGUOUS_EFFECT"
            transferable = linked
        else:
            transferable = linked
            if transferable:
                p = (prior["alpha"] + history["successes"]) / (
                    prior["alpha"] + prior["beta"] + history["successes"] + history["failures"]
                )
            else:
                p = prior["alpha"] / (prior["alpha"] + prior["beta"])
            status = "PROPOSE_ROUTE" if transferable and p >= threshold else "VERIFY_CURRENT_B"
        if history["dependency"] == "unknown" or case["effect_state"] == "ambiguous":
            p = (prior["alpha"] + history["successes"]) / (
                prior["alpha"] + prior["beta"] + history["successes"] + history["failures"]
            ) if transferable else prior["alpha"] / (prior["alpha"] + prior["beta"])
        rows.append({
            "case_id": case["case_id"],
            "current_b": dict(current),
            "effect_state": case["effect_state"],
            "transfer_eligible": transferable,
            "transferred_success_probability": round(p, 6),
            "decision": status,
            "open_obligations": sorted(case["open_obligations"]),
            "included_history_artifact_ids": [history["task_id"] + ":" + str(history["generation"])] if transferable else [],
        })
    return {"schema": "context-success-history-candidate-v1",
            "allocation_id": data["allocation_id"],
            "frozen_main_sha": data["frozen_main_sha"],
            "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="fixtures.json")
    ap.add_argument("--output", default="candidate_output.json")
    args = ap.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    result = build(payload)
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(result["rows"]), "output": args.output}, sort_keys=True))


if __name__ == "__main__":
    main()
