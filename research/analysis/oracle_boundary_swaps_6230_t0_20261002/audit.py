"""Independent structural and adversarial audit; does not import candidate."""
from copy import deepcopy


ARMS = ("actual", "observation_oracle", "execution_oracle", "joint")
CASES = ("semantic_limited", "observation_limited", "execution_limited", "joint_only", "ambiguous", "answer_leakage", "reset_contamination")
EXPECTED = {
    "semantic_limited": (False, False, False, False),
    "observation_limited": (False, True, False, True),
    "execution_limited": (False, False, True, True),
    "joint_only": (False, False, False, True),
}


def _check(raw):
    errors = []
    if raw.get("schema") != "oracle-boundary-swaps-6230-t0-v1" or tuple(raw.get("arms", ())) != ARMS or tuple(raw.get("cases", ())) != CASES:
        errors.append("schema, arm order, or complete case denominator differs")
    rows = raw.get("outcomes", [])
    index = {(r.get("case_id"), r.get("arm")): r for r in rows}
    if len(rows) != len(CASES) * len(ARMS) or len(index) != len(rows) or set(index) != {(c, a) for c in CASES for a in ARMS}:
        errors.append("missing, duplicate, or unregistered arm outcome")
        return errors
    for case, expected in EXPECTED.items():
        observed = tuple(index[case, arm].get("effect_correct") for arm in ARMS)
        if observed != expected:
            errors.append("planted boundary class not distinguished: " + case)
    for case in CASES:
        cohort = [index[case, arm] for arm in ARMS]
        if len({r.get("initial_state_digest") for r in cohort}) != 1:
            errors.append("cross-arm reset/carryover contamination: " + case)
    for row in rows:
        arm, case = row["arm"], row["case_id"]
        if row.get("safety_bypassed"):
            errors.append("safety bypass counted or present")
        if arm in ("execution_oracle", "joint") and row.get("executed_intent") != row.get("model_intent"):
            errors.append("execution oracle changed frozen semantic intent")
        leaked = case == "answer_leakage" and arm in ("observation_oracle", "joint")
        if leaked and (row.get("oracle_admissible") or row.get("effect_correct") or row.get("disposition") != "REJECTED_LEAKAGE"):
            errors.append("answer-leaking oracle was accepted or credited")
        if case == "ambiguous" and (row.get("disposition") != "UNDEFINED" or row.get("effect_correct")):
            errors.append("ambiguous task was assigned a success label")
        if arm in ("observation_oracle", "joint") and not leaked:
            if any(row.get(k) for k in ("oracle_contains_answer", "oracle_contains_plan", "oracle_contains_authorization")):
                errors.append("oracle includes answer, plan, or privileged authorization")
    return errors


def audit(raw):
    errors = _check(raw)
    controls = {}
    if not errors:
        mutations = {
            "drop_outcome": lambda x: x["outcomes"].pop(),
            "duplicate_arm": lambda x: x["outcomes"].append(deepcopy(x["outcomes"][0])),
            "alter_effect": lambda x: x["outcomes"][4].__setitem__("effect_correct", True),
            "repair_semantics_in_execution_oracle": lambda x: x["outcomes"][2].__setitem__("executed_intent", "requested_target"),
            "accept_answer_leak": lambda x: x["outcomes"][21].__setitem__("oracle_admissible", True),
            "score_ambiguous": lambda x: x["outcomes"][16].__setitem__("effect_correct", True),
            "carry_state_across_arms": lambda x: x["outcomes"][27].__setitem__("initial_state_digest", "prior-arm-state"),
        }
        for name, mutation in mutations.items():
            altered = deepcopy(raw)
            mutation(altered)
            controls[name] = bool(_check(altered))
        if not all(controls.values()):
            errors.append("at least one corruption control was accepted")
    return {"status": "PASS_METHOD_SCOPED" if not errors and len(controls) == 7 else "FAIL_METHOD", "errors": errors,
            "mutation_controls_passed": sum(controls.values()), "mutation_controls": controls,
            "auditor": "independent-raw-only-6230-t0-v1"}
