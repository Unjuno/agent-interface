"""Independent exact-row and paired-intent audit; does not import candidate.py."""
from copy import deepcopy


ARMS = ("actual", "observation_oracle", "execution_oracle", "joint")
TABLE = {
    "semantic_limited": ("requested_target", True, False, (
        ("wrong_target", "wrong_target", False), ("wrong_target", "wrong_target", False),
        ("wrong_target", "wrong_target", False), ("wrong_target", "wrong_target", False))),
    "observation_limited": ("requested_target", True, False, (
        ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", True),
        ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", True))),
    "execution_limited": ("requested_target", True, False, (
        ("requested_target", "wrong_target", False), ("requested_target", "wrong_target", False),
        ("requested_target", "requested_target", True), ("requested_target", "requested_target", True))),
    "joint_only": ("requested_target", True, False, (
        ("wrong_target", "wrong_target", False), ("requested_target", "wrong_target", False),
        ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", True))),
    "ambiguous": ("nonunique", False, False, (("unspecified", "unspecified", False),) * 4),
    "answer_leakage": ("requested_target", True, True, (
        ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", False),
        ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", False))),
    "reset_contamination": ("requested_target", True, False, (
        ("requested_target", "wrong_target", False), ("requested_target", "wrong_target", False),
        ("requested_target", "requested_target", True), ("requested_target", "requested_target", True))),
}
CASES = tuple(TABLE)


def _expected():
    rows = []
    for case, (truth, defined, leak_case, matrix) in TABLE.items():
        for index, arm in enumerate(ARMS):
            intent, executed, correct = matrix[index]
            leaked = leak_case and arm in ("observation_oracle", "joint")
            rows.append({
                "case_id": case, "arm": arm, "initial_state_digest": "seed-6230-successor-state-0",
                "model_intent": intent, "executed_intent": executed, "effect_truth": truth,
                "effect_correct": correct, "disposition": "UNDEFINED" if not defined else "REJECTED_LEAKAGE" if leaked else "OBSERVED",
                "oracle_admissible": not leaked, "oracle_contains_answer": leaked,
                "oracle_contains_plan": False, "oracle_contains_authorization": False,
                "safety_bypassed": False,
            })
    return rows


def _check(raw):
    errors = []
    expected = _expected()
    if raw.get("schema") != "oracle-boundary-swaps-6230-t0-successor-v1" or tuple(raw.get("cases", ())) != CASES or tuple(raw.get("arms", ())) != ARMS:
        errors.append("schema or frozen case/arm denominator differs")
    rows = raw.get("outcomes", [])
    if rows != expected:
        errors.append("raw rows differ from independent paired-intent truth table")
    indexed = {(r.get("case_id"), r.get("arm")): r for r in rows}
    if len(rows) == len(expected) and len(indexed) == len(rows):
        for case in CASES:
            if indexed[case, "execution_oracle"].get("model_intent") != indexed[case, "actual"].get("model_intent"):
                errors.append("execution-only intent differs from matched actual frozen intent: " + case)
            for arm in ("execution_oracle", "joint"):
                row = indexed[case, arm]
                if row.get("executed_intent") != row.get("model_intent"):
                    errors.append("exact actuator changed semantic intent: " + case + "/" + arm)
    return errors


def audit(raw):
    errors = _check(raw)
    controls = {}
    if not errors:
        def paired_intent(x):
            row = next(r for r in x["outcomes"] if r["case_id"] == "semantic_limited" and r["arm"] == "execution_oracle")
            row["model_intent"] = row["executed_intent"] = "requested_target"
        mutations = {
            "drop_outcome": lambda x: x["outcomes"].pop(),
            "alter_outcome": lambda x: x["outcomes"][4].__setitem__("effect_correct", True),
            "paired_intent_divergence_with_local_equality_intact": paired_intent,
            "accept_answer_leak": lambda x: x["outcomes"][21].__setitem__("oracle_admissible", True),
            "score_ambiguous": lambda x: x["outcomes"][16].__setitem__("effect_correct", True),
            "carry_state": lambda x: x["outcomes"][27].__setitem__("initial_state_digest", "prior-arm-state"),
            "safety_bypass": lambda x: x["outcomes"][3].__setitem__("safety_bypassed", True),
            "inject_plan": lambda x: x["outcomes"][1].__setitem__("oracle_contains_plan", True),
        }
        for name, mutation in mutations.items():
            altered = deepcopy(raw)
            mutation(altered)
            controls[name] = bool(_check(altered))
        if not all(controls.values()):
            errors.append("one or more corruption controls were accepted")
    return {"status": "PASS_METHOD_SCOPED" if not errors and len(controls) == 8 else "FAIL_METHOD", "errors": errors,
            "mutation_controls_passed": sum(controls.values()), "mutation_controls": controls,
            "auditor": "independent-exact-paired-intent-6230-t0s2-v1"}
