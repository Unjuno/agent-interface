"""Independent raw-only verifier; deliberately imports no candidate code."""
import argparse
import copy
import json
from pathlib import Path


def expected(data):
    rows = []
    baseline = data["prior"]["alpha"] / (data["prior"]["alpha"] + data["prior"]["beta"])
    for item in data["cases"]:
        h = item["history"]
        b = data["current_b"]
        can_transfer = all((
            h["artifact_scope"] == "declared_shared_predictive",
            h["dependency"] == "same_latent_regime",
            h["artifact_state"] == "completed",
            h["capability_id"] == b["capability_id"],
            h["route_precondition_sha256"] == b["route_precondition_sha256"],
        ))
        probability = ((data["prior"]["alpha"] + h["successes"]) /
                       (data["prior"]["alpha"] + data["prior"]["beta"] + h["successes"] + h["failures"])) if can_transfer else baseline
        if h["dependency"] == "unknown":
            decision = "HOLD_UNKNOWN_DEPENDENCY"
            can_transfer = False
            probability = baseline
        elif item["effect_state"] == "ambiguous":
            decision = "HOLD_AMBIGUOUS_EFFECT"
        else:
            decision = "PROPOSE_ROUTE" if can_transfer and probability >= data["proposal_threshold"] else "VERIFY_CURRENT_B"
        rows.append({
            "case_id": item["case_id"],
            "current_b": copy.deepcopy(b),
            "effect_state": item["effect_state"],
            "transfer_eligible": can_transfer,
            "transferred_success_probability": round(probability, 6),
            "decision": decision,
            "open_obligations": sorted(item["open_obligations"]),
            "included_history_artifact_ids": [h["task_id"] + ":" + str(h["generation"])] if can_transfer else [],
        })
    return {"schema": "context-success-history-candidate-v1",
            "allocation_id": data["allocation_id"],
            "frozen_main_sha": data["frozen_main_sha"],
            "rows": rows}


def verify(data, raw):
    return raw == expected(data)


def mutations(data, raw):
    results = {}
    edits = {}
    edits["drop_open_obligation"] = copy.deepcopy(raw)
    edits["drop_open_obligation"]["rows"][4]["open_obligations"] = []
    edits["clear_ambiguous_effect"] = copy.deepcopy(raw)
    edits["clear_ambiguous_effect"]["rows"][4]["effect_state"] = "none"
    edits["transfer_across_independent_regime"] = copy.deepcopy(raw)
    edits["transfer_across_independent_regime"]["rows"][1]["transfer_eligible"] = True
    edits["transfer_across_independent_regime"]["rows"][1]["transferred_success_probability"] = 0.75
    edits["leak_private_history"] = copy.deepcopy(raw)
    edits["leak_private_history"]["rows"][6]["included_history_artifact_ids"] = ["task-A-114:3"]
    edits["stale_current_observation"] = copy.deepcopy(raw)
    edits["stale_current_observation"]["rows"][0]["current_b"]["observation_sha256"] = "0" * 64
    edits["transfer_after_precondition_change"] = copy.deepcopy(raw)
    edits["transfer_after_precondition_change"]["rows"][2]["transfer_eligible"] = True
    for name, changed in edits.items():
        results[name] = not verify(data, changed)
    return results


def audit(data, raw):
    want = expected(data)
    controls = mutations(data, raw)
    checks = {
        "exact_raw_reconstruction": raw == want,
        "all_rows_unique_and_complete": len(raw.get("rows", [])) == len(data["cases"]) and
            len({r.get("case_id") for r in raw.get("rows", [])}) == len(data["cases"]),
        "same_streak_regime_discriminator": raw["rows"][0]["transferred_success_probability"] == 0.75 and
            raw["rows"][1]["transferred_success_probability"] == 0.5 and
            raw["rows"][0]["decision"] != raw["rows"][1]["decision"],
        "changed_precondition_resets_transfer": not raw["rows"][2]["transfer_eligible"],
        "weak_history_remains_below_threshold": raw["rows"][3]["transferred_success_probability"] == 0.25 and
            raw["rows"][3]["decision"] == "VERIFY_CURRENT_B",
        "ambiguous_effect_holds_and_preserves_obligation": raw["rows"][4]["decision"] == "HOLD_AMBIGUOUS_EFFECT" and
            raw["rows"][4]["open_obligations"] == ["obligation-A-effect-77"],
        "unknown_dependency_holds": raw["rows"][5]["decision"] == "HOLD_UNKNOWN_DEPENDENCY" and
            not raw["rows"][5]["transfer_eligible"],
        "private_history_not_exposed": raw["rows"][6]["included_history_artifact_ids"] == [],
        "capability_mismatch_resets_transfer": not raw["rows"][7]["transfer_eligible"],
        "six_mutations_rejected": all(controls.values()),
    }
    return {"disposition": "PASS_METHOD_SCOPED" if all(checks.values()) else "STOP_AUDIT_MISMATCH",
            "checks": checks, "mutation_controls": controls,
            "expected_rows": len(data["cases"]), "reconstructed_rows": len(raw.get("rows", []))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="fixtures.json")
    ap.add_argument("--candidate-output", default="candidate_output.json")
    ap.add_argument("--output", default="audit_report.json")
    args = ap.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    raw = json.loads(Path(args.candidate_output).read_text(encoding="utf-8"))
    report = audit(data, raw)
    Path(args.output).write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
