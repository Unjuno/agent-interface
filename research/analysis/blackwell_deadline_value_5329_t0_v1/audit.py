import copy
import hashlib
import json
import sys
from pathlib import Path


EXPECTED = {
    "deadline": 3,
    "safe_prepare_utility": 2,
    "commit_utility": 10,
    "state_prior": {"safe": 0.5, "blocked": 0.5},
    "raw_signal": {"safe": "CLEAR", "blocked": "BLOCKED"},
    "garble": {"CLEAR": "TARGET_PRESENT", "BLOCKED": "TARGET_PRESENT"},
    "arms": {"RAW_NOW": ["raw", 1], "RAW_DELAYED": ["raw", 6],
             "COMPRESSED_NOW": ["compressed", 1], "COMPRESSED_DELAYED": ["compressed", 6]},
}
STATES = ("safe", "blocked")


def independent_decision(state, channel, observation, arrival, deadline):
    if arrival > deadline:
        return "WAIT", False, 0
    if channel == "raw" and observation == "CLEAR" and state == "safe":
        return "IRREVERSIBLE_COMMIT", True, 10
    return "SAFE_REVERSIBLE_PREPARE", True, 2


def recompute(doc):
    errors = []
    for field, value in EXPECTED.items():
        if doc.get(field) != value:
            errors.append(f"definition_mismatch:{field}")
    expected_rows = []
    for arm, spec in EXPECTED["arms"].items():
        channel, arrival = spec
        for state in STATES:
            raw = EXPECTED["raw_signal"][state]
            obs = raw if channel == "raw" else EXPECTED["garble"][raw]
            action, admitted, score = independent_decision(state, channel, obs, arrival, EXPECTED["deadline"])
            expected_rows.append({"arm": arm, "channel": channel, "arrival": arrival,
                                  "deadline": EXPECTED["deadline"], "state": state,
                                  "observation": obs, "action": action, "admitted": admitted,
                                  "unsafe_effect": action == "IRREVERSIBLE_COMMIT" and state != "safe",
                                  "utility": score})
    if doc.get("rows") != expected_rows:
        errors.append("arm_rows_do_not_match_independent_oracle")
    expected_safety = []
    for state in STATES:
        obs = EXPECTED["garble"][EXPECTED["raw_signal"][state]]
        expected_safety.append({"state": state, "channel": "compressed", "arrival": 1,
                                "observation": obs, "requested_action": "IRREVERSIBLE_COMMIT",
                                "admitted": False, "unsafe_effect": False,
                                "reason": "INSUFFICIENT_INFORMATION"})
    if doc.get("compressed_irreversible_probes") != expected_safety:
        errors.append("compressed_irreversible_safety_gate_mismatch")
    by_arm = {}
    for row in expected_rows:
        by_arm[row["arm"]] = by_arm.get(row["arm"], 0) + EXPECTED["state_prior"][row["state"]] * row["utility"]
    if not (by_arm["RAW_NOW"] > by_arm["COMPRESSED_NOW"]):
        errors.append("equal_time_raw_not_strictly_more_decision_valuable")
    if not (by_arm["COMPRESSED_NOW"] > by_arm["RAW_DELAYED"]):
        errors.append("deadline_timing_does_not_reverse_pairwise_value")
    if any(r["unsafe_effect"] for r in expected_rows) or any(r["unsafe_effect"] for r in expected_safety):
        errors.append("unsafe_effect_admitted")
    return {"errors": errors, "expected_rows": expected_rows,
            "expected_safety": expected_safety, "expected_utility_by_arm": by_arm}


def corruption_suite(doc):
    mutations = [
        ("break_garbling_map", lambda x: x["garble"].update(BLOCKED="BLOCKED")),
        ("inflate_compressed_now_utility", lambda x: x["rows"][4].update(utility=10)),
        ("admit_compressed_commit", lambda x: x["compressed_irreversible_probes"][0].update(admitted=True, unsafe_effect=True)),
        ("move_deadline_after_raw_arrival", lambda x: x.update(deadline=7)),
        ("forge_equal_time_claim", lambda x: x["rows"][0].update(observation="TARGET_PRESENT")),
    ]
    results = []
    for name, mutate in mutations:
        mutant = copy.deepcopy(doc)
        mutate(mutant)
        rejected = bool(recompute(mutant)["errors"])
        results.append({"name": name, "rejected": rejected})
    return results


def audit_document(doc):
    base = recompute(doc)
    controls = corruption_suite(doc)
    if len(controls) != 5 or not all(item["rejected"] for item in controls):
        base["errors"].append("corruption_control_escaped")
    return {"schema": "issue5329-blackwell-deadline-audit-v1",
            "errors": base["errors"], "utility_by_arm": base["expected_utility_by_arm"],
            "raw_rows": len(doc.get("rows", [])), "safety_probes": len(doc.get("compressed_irreversible_probes", [])),
            "corruptions": controls,
            "equal_time_raw_gt_compressed": base["expected_utility_by_arm"].get("RAW_NOW", 0) > base["expected_utility_by_arm"].get("COMPRESSED_NOW", 0),
            "compressed_now_gt_raw_delayed": base["expected_utility_by_arm"].get("COMPRESSED_NOW", 0) > base["expected_utility_by_arm"].get("RAW_DELAYED", 0),
            "disposition": "METHOD_PASS_SCOPED" if not base["errors"] else "FAIL_AUDIT"}


def main():
    raw = Path(sys.argv[1]).read_bytes()
    doc = json.loads(raw)
    result = audit_document(doc)
    result["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if not result["errors"] else 1)


if __name__ == "__main__":
    main()
