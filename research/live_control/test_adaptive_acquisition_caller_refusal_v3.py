"""Preserve compiled refusal progress at the existing caller v3 boundary.

All adapters below are inert. No GUI input or real admission is performed.
"""
import unittest

from adaptive_acquisition_caller_v3 import run
from runtime.core_v1 import compiled_gui

ROWS = []


def spec():
    return {"target": "inert-target", "route": "reuse",
            "coarse_origin": "caller_provided", "provided_coarse": None,
            "cached_target": {"ref": "inert-target"}, "local_repair_on": [],
            "repair_on": [], "session_id": "inert-no-desktop"}


def call(execution, label):
    counts = {"execute": 0, "verify_effect": 0}

    def execute(payload):
        counts["execute"] += 1
        return execution(payload) if callable(execution) else execution

    def verify(payload):
        counts["verify_effect"] += 1
        return {"status": "succeeded"}

    result = run(spec(), {
        "reuse_revalidate": lambda _: {"status": "revalidated"},
        "final_revalidate": lambda _: {"status": "revalidated"},
        "execute": execute, "verify_effect": verify})
    ROWS.append({"case": label, "execution": execution if not callable(execution) else "actual_compiled_run",
                 "calls": counts.copy(), "caller": result})
    return result, counts


class CallerRefusalV3Test(unittest.TestCase):
    def check_yield(self, result, counts, completed):
        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(result["reason"], "execution_refused")
        self.assertEqual(result["execution_progress"], {
            "status": "safe_yield", "reason": "execution_refused",
            "completed_actions": completed})
        self.assertEqual(result["delivery"], "confirmed_partial" if completed else "not_attempted")
        self.assertEqual(result["input_authority"], "consumed_by_recorded_execute_stage" if completed else "none")
        self.assertEqual(counts, {"execute": 1, "verify_effect": 0})
        self.assertEqual(result["accounting"]["attempted_calls"], 0)

    def test_zero_action_refusal_remains_no_input(self):
        result, counts = call({"status": "safe_yield", "reason": "execution_refused",
                               "completed_actions": 0}, "zero-refusal")
        self.check_yield(result, counts, 0)

    def test_partial_refusal_retains_completed_prefix(self):
        result, counts = call({"status": "safe_yield", "reason": "execution_refused",
                               "completed_actions": 1}, "partial-refusal")
        self.check_yield(result, counts, 1)

    def test_malformed_refusals_still_fail_closed(self):
        valid = {"status": "safe_yield", "reason": "execution_refused", "completed_actions": 0}
        mutations = [
            ("boolean-count", {**valid, "completed_actions": False}),
            ("negative-count", {**valid, "completed_actions": -1}),
            ("float-count", {**valid, "completed_actions": 0.0}),
            ("missing-count", {"status": "safe_yield", "reason": "execution_refused"}),
            ("extra-target", {**valid, "target": {"point": [1, 2]}}),
            ("unknown-reason", {**valid, "reason": "invented_reason"}),
            ("wrong-status", {**valid, "status": "completed"}),
        ]
        for label, execution in mutations:
            with self.subTest(label=label):
                result, counts = call(execution, label)
                self.assertEqual(result["outcome"], "CALLER_FAILED")
                self.assertIsNone(result["execution_progress"])
                self.assertEqual(counts["verify_effect"], 0)

    def test_supported_yield_and_success_are_unchanged(self):
        result, counts = call({"status": "safe_yield", "reason": "cancelled", "completed_actions": 0}, "cancelled-control")
        self.assertEqual((result["outcome"], result["reason"], result["input_authority"]),
                         ("EXECUTION_INCOMPLETE", "cancelled", "none"))
        self.assertEqual(counts["verify_effect"], 0)
        result, counts = call({"status": "completed"}, "completed-control")
        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(counts["verify_effect"], 1)

    def test_actual_compiled_refusal_composes_before_or_after_prefix(self):
        for completed in (0, 1):
            with self.subTest(completed=completed):
                inner = []
                state = {"sequence": 0, "execute": 0, "effect": 0}
                interface = {
                    "format": "compiled-gui-interface-v1", "interface_id": "inert-composition",
                    "session_scope": "inert-no-lease", "surface": "inert-no-desktop",
                    "predicates": ["ready", "done"],
                    "symbols": {"target": {"kind": "target_reference", "target_reference": "inert",
                         "identity_predicate": "ready", "dependencies": ["ready"]}},
                    "actions": {"try": {"target_symbol": "target", "operation": "inert",
                         "expected_effect": {"done": True}}},
                    "method": {"name": "inert", "version": "1", "initial_state": "start",
                         "max_transitions": 2, "max_runtime_ms": 1000,
                         "states": {name: {"branches": [{"when": {"ready": True}, "outcome": "action",
                             "action": "try", "next_state": "next", "reason": None}]}
                                    for name in ("start", "next")}}}

                def observe(_):
                    state["sequence"] += 1
                    seq = state["sequence"]
                    return {"sequence": seq, "captured_ns": seq, "surface": "inert-no-desktop",
                            "predicates": {"ready": True, "done": seq > 1},
                            "evidence_ref": "inert-frame-" + str(seq), "evidence_digest": "digest-" + str(seq)}

                def execute(_):
                    index = state["execute"]; state["execute"] += 1
                    if index < completed:
                        return {"status": "completed", "action_id": "inert-action", "effect_ref": "inert-effect",
                                "release": {"verified": True, "keys_down": [], "buttons_down": []}}
                    return {"status": "refused", "input_dispatched": False, "action_id": None, "effect_ref": None,
                            "release": {"verified": False, "keys_down": [], "buttons_down": []}}

                def effect(_):
                    state["effect"] += 1
                    return {"status": "succeeded", "evidence_ref": "inert-effect-proof"}

                def compiled(_):
                    receipt = compiled_gui.run(interface, {
                        "observe": observe, "cancelled": lambda: False, "execute": execute, "verify_effect": effect,
                        "admit": lambda value: {"eligible": True, "status": "revalidated",
                            "authorization": "INERT_TEST_ONLY_NO_AUTHORITY", "expected_sequence": value["observation"]["sequence"],
                            "valid_until_ns": 999999999}}, clock=lambda: state["sequence"])
                    inner.append(receipt)
                    return {"status": "safe_yield", "reason": receipt["reason"],
                            "completed_actions": receipt["completed_transitions"]}

                result, counts = call(compiled, "compiled-prefix-" + str(completed))
                ROWS[-1]["compiled"] = inner[0]
                ROWS[-1]["compiled_calls"] = state.copy()
                self.assertEqual(inner[0]["outcome"], "SAFE_YIELD")
                self.assertEqual(inner[0]["reason"], "execution_refused")
                self.assertEqual(inner[0]["completed_transitions"], completed)
                self.assertEqual(state["execute"], completed + 1)
                self.assertEqual(state["effect"], completed)
                self.check_yield(result, counts, completed)


if __name__ == "__main__":
    unittest.main()
