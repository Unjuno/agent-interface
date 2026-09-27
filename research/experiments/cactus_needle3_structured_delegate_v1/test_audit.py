import copy
import json
import unittest
from pathlib import Path

from audit import audit


HERE = Path(__file__).resolve().parent
CASES = json.loads((HERE / "CASES.json").read_text(encoding="utf-8"))
FREEZE = {
    "source_sha256": {},
    "candidate": CASES["candidate"],
    "docker_image": "python@sha256:fixture",
}
FREEZE_SHA = "0" * 64


def valid_fixture():
    model_rows, baseline_rows = [], []
    all_turns = []
    for case in CASES["cases"]:
        turns = []
        state = copy.deepcopy(case["state"])
        for index, expected in enumerate(case["expected"]):
            before = copy.deepcopy(state)
            if expected["name"] == "CLICK" and expected["arguments"].get("target") == "toggle_email_reminders":
                state["email_reminders"] = not state["email_reminders"]
                status = "ACCEPT_EFFECT"
            elif expected["name"] == "SET_FIELD":
                field, value = expected["arguments"]["field"], expected["arguments"]["value"]
                state.setdefault("staged", {})[field] = value
                state[field] = value
                status = "ACCEPT_STAGED"
            elif expected["name"] == "CLICK" and expected["arguments"].get("target") == "save_settings":
                state.update(state.get("staged", {}))
                state["saved"] = True
                status = "ACCEPT_EFFECT"
            else:
                status = "ACCEPT_NON_ACTION"
            turn = {
                "case_id": case["id"], "turn": index,
                "proposed_call_count": 1, "proposal": expected,
                "proposal_exact_match": True, "expected_call": expected,
                "admission": {"status": status}, "state_before": before,
                "state_after": copy.deepcopy(state), "first_inference": len(all_turns) == 0,
                "decision_latency_ms": 10.0,
            }
            turns.append(turn)
            all_turns.append(turn)
        model_rows.append({
            "id": case["id"], "initial_state": copy.deepcopy(case["state"]),
            "turns": turns, "terminal_state": state,
            "all_expected_turns_exact": True,
            "exact_effect_match": all(state.get(k) == v for k, v in case["expected_effect"].items()),
        })
        base_state = copy.deepcopy(case["state"])
        base_calls = [{"proposal": expected, "admission": {"status": "ACCEPT_BASELINE"}} for expected in case["expected"]]
        for expected in case["expected"]:
            if expected["name"] == "CLICK" and expected["arguments"].get("target") == "toggle_email_reminders":
                base_state["email_reminders"] = not base_state["email_reminders"]
            elif expected["name"] == "SET_FIELD":
                field, value = expected["arguments"]["field"], expected["arguments"]["value"]
                base_state.setdefault("staged", {})[field] = value
                base_state[field] = value
            elif expected["name"] == "CLICK" and expected["arguments"].get("target") == "save_settings":
                base_state.update(base_state.get("staged", {}))
                base_state["saved"] = True
        baseline_rows.append({"id": case["id"], "calls": base_calls, "terminal_state": base_state,
                              "exact_effect_match": all(base_state.get(k) == v for k, v in case["expected_effect"].items())})
    warm = [turn["decision_latency_ms"] for turn in all_turns if not turn["first_inference"]]
    warm_sorted = sorted(warm)
    import math
    p95 = warm_sorted[math.ceil(.95 * len(warm_sorted)) - 1]
    return {
        "schema": "cactus-needle3-formal-result-v1", "allocation": CASES["allocation"],
        "freeze_sha256": FREEZE_SHA, "source_sha256": {},
        "formal_invocations": 1, "reruns": 0, "replacements": 0, "tuning": 0,
        "model_rows": model_rows, "guarded_macro_rows": baseline_rows,
        "warm_decision_ms": warm, "warm_p95_ms": p95,
        "runtime": {"network_disabled": True, "telemetry_disabled": True,
                    "model_sha256": CASES["candidate"]["weights_sha256"],
                    "client_wheel_sha256": CASES["candidate"]["client_wheel_sha256"],
                    "engine_wheel_sha256": CASES["candidate"]["engine_wheel_sha256"],
                    "image": "python@sha256:fixture", "cuda_visible_devices": "-1",
                    "cgroup_memory_peak": "1024", "cgroup_memory_max": "999999"},
    }


class AuditorMutationTests(unittest.TestCase):
    def test_clean_copy_has_zero_audit_errors(self):
        report = audit(valid_fixture(), CASES, FREEZE, FREEZE_SHA)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["decision"], "FAIL_NO_VALUE_OVER_EXPLICIT_BASELINE")

    def test_dropped_row_is_rejected(self):
        result = valid_fixture()
        result["model_rows"].pop()
        self.assertIn("model_case_count_or_order", audit(result, CASES, FREEZE, FREEZE_SHA)["errors"])

    def test_reordered_rows_are_rejected(self):
        result = valid_fixture()
        result["model_rows"][0], result["model_rows"][1] = result["model_rows"][1], result["model_rows"][0]
        self.assertIn("model_case_count_or_order", audit(result, CASES, FREEZE, FREEZE_SHA)["errors"])

    def test_safety_proposal_corruption_is_rejected(self):
        result = valid_fixture()
        result["model_rows"][3]["turns"][0]["proposal"] = {"name": "CLICK", "arguments": {"target": "delete_workspace"}}
        report = audit(result, CASES, FREEZE, FREEZE_SHA)
        self.assertTrue(report["yield_errors"])

    def test_gate_latency_field_corruption_is_rejected(self):
        result = valid_fixture()
        result["warm_p95_ms"] = 0
        self.assertIn("warm_p95_mismatch", audit(result, CASES, FREEZE, FREEZE_SHA)["errors"])

    def test_unbounded_rerun_claim_is_rejected(self):
        result = valid_fixture()
        result["reruns"] = 1
        self.assertIn("formal_run_cardinality_or_tuning", audit(result, CASES, FREEZE, FREEZE_SHA)["errors"])


if __name__ == "__main__":
    unittest.main()
