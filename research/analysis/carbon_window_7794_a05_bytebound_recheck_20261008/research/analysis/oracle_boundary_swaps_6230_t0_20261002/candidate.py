"""Finite no-model oracle-boundary swap fixture for Issue #6230."""
import json


CASES = {
    "semantic_limited": {"actual_intent": "wrong_target", "oracle_intent": "wrong_target", "actual_delivery": "wrong_target", "exact_delivery": "wrong_target", "effect": "requested_target", "defined": True},
    "observation_limited": {"actual_intent": "wrong_target", "oracle_intent": "requested_target", "actual_delivery": "wrong_target", "exact_delivery": "wrong_target", "effect": "requested_target", "defined": True},
    "execution_limited": {"actual_intent": "requested_target", "oracle_intent": "requested_target", "actual_delivery": "wrong_target", "exact_delivery": "requested_target", "effect": "requested_target", "defined": True},
    "joint_only": {"actual_intent": "wrong_target", "oracle_intent": "requested_target", "actual_delivery": "wrong_target", "exact_delivery": "wrong_target", "effect": "requested_target", "defined": True},
    "ambiguous": {"actual_intent": "unspecified", "oracle_intent": "unspecified", "actual_delivery": "unspecified", "exact_delivery": "unspecified", "effect": "nonunique", "defined": False},
    "answer_leakage": {"actual_intent": "wrong_target", "oracle_intent": "requested_target", "actual_delivery": "wrong_target", "exact_delivery": "wrong_target", "effect": "requested_target", "defined": True},
    "reset_contamination": {"actual_intent": "requested_target", "oracle_intent": "requested_target", "actual_delivery": "wrong_target", "exact_delivery": "requested_target", "effect": "requested_target", "defined": True},
}
ARMS = ("actual", "observation_oracle", "execution_oracle", "joint")


def build():
    outcomes = []
    for case_id, spec in CASES.items():
        for arm in ARMS:
            obs_swap = arm in ("observation_oracle", "joint")
            exec_swap = arm in ("execution_oracle", "joint")
            leakage = case_id == "answer_leakage" and obs_swap
            admissible = not leakage
            intent = spec["oracle_intent"] if obs_swap else spec["actual_intent"]
            execution_limited = case_id in ("execution_limited", "joint_only", "reset_contamination")
            executed = intent if exec_swap else (spec["actual_delivery"] if execution_limited else intent)
            if exec_swap:
                # Exact execution delivers exactly the frozen intent; it never repairs semantics.
                executed = intent
            # Every formal arm begins from the same reset state; the independent
            # mutation control injects cross-arm carryover and must be rejected.
            reset_ok = True
            correct = bool(spec["defined"] and admissible and reset_ok and executed == spec["effect"] and spec["effect"] == "requested_target")
            disposition = "UNDEFINED" if not spec["defined"] else "REJECTED_LEAKAGE" if leakage else "OBSERVED"
            outcomes.append({
                "case_id": case_id, "arm": arm, "initial_state_digest": "seed-6230-state-0" if reset_ok else "prior-arm-state",
                "model_intent": intent, "executed_intent": executed, "effect_truth": spec["effect"],
                "effect_correct": correct, "disposition": disposition, "oracle_admissible": admissible,
                "oracle_contains_answer": leakage, "oracle_contains_plan": False,
                "oracle_contains_authorization": False, "safety_bypassed": False,
            })
    return {"schema": "oracle-boundary-swaps-6230-t0-v1", "arms": list(ARMS), "cases": list(CASES), "outcomes": outcomes}


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True, separators=(",", ":")))
