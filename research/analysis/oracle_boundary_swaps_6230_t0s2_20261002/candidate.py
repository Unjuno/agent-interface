"""Fresh paired-intent T0 successor for Issue #6230; finite and no-model."""
import json


ARMS = ("actual", "observation_oracle", "execution_oracle", "joint")
CASES = {
    "semantic_limited": {
        "rows": (("wrong_target", "wrong_target", False),) * 4, "truth": "requested_target", "defined": True,
    },
    "observation_limited": {
        "rows": (("wrong_target", "wrong_target", False), ("requested_target", "requested_target", True),
                 ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", True)),
        "truth": "requested_target", "defined": True,
    },
    "execution_limited": {
        "rows": (("requested_target", "wrong_target", False), ("requested_target", "wrong_target", False),
                 ("requested_target", "requested_target", True), ("requested_target", "requested_target", True)),
        "truth": "requested_target", "defined": True,
    },
    "joint_only": {
        "rows": (("wrong_target", "wrong_target", False), ("requested_target", "wrong_target", False),
                 ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", True)),
        "truth": "requested_target", "defined": True,
    },
    "ambiguous": {
        "rows": (("unspecified", "unspecified", False),) * 4, "truth": "nonunique", "defined": False,
    },
    "answer_leakage": {
        "rows": (("wrong_target", "wrong_target", False), ("requested_target", "requested_target", False),
                 ("wrong_target", "wrong_target", False), ("requested_target", "requested_target", False)),
        "truth": "requested_target", "defined": True,
    },
    "reset_contamination": {
        "rows": (("requested_target", "wrong_target", False), ("requested_target", "wrong_target", False),
                 ("requested_target", "requested_target", True), ("requested_target", "requested_target", True)),
        "truth": "requested_target", "defined": True,
    },
}


def build():
    outcomes = []
    for case, spec in CASES.items():
        for index, arm in enumerate(ARMS):
            intent, executed, correct = spec["rows"][index]
            leakage = case == "answer_leakage" and arm in ("observation_oracle", "joint")
            disposition = "UNDEFINED" if not spec["defined"] else "REJECTED_LEAKAGE" if leakage else "OBSERVED"
            outcomes.append({
                "case_id": case, "arm": arm, "initial_state_digest": "seed-6230-successor-state-0",
                "model_intent": intent, "executed_intent": executed, "effect_truth": spec["truth"],
                "effect_correct": correct, "disposition": disposition, "oracle_admissible": not leakage,
                "oracle_contains_answer": leakage, "oracle_contains_plan": False,
                "oracle_contains_authorization": False, "safety_bypassed": False,
            })
    return {"schema": "oracle-boundary-swaps-6230-t0-successor-v1", "cases": list(CASES), "arms": list(ARMS), "outcomes": outcomes}


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True, separators=(",", ":")))
