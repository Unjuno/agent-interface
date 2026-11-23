"""Composition check for adaptive caller v3 and the bounded compiled GUI runtime."""
import copy
import unittest

from research.live_control.adaptive_acquisition_caller_v3 import run as run_caller
from runtime.core_v1.compiled_gui import run as run_compiled


USAGE = {
    "input_tokens": 100,
    "cached_input_tokens": 20,
    "cache_write_input_tokens": 0,
    "output_tokens": 12,
    "reasoning_output_tokens": 3,
}


class Clock:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 10
        return self.value


def compiled_interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "synthetic-form-flow-v1",
        "session_scope": "synthetic-private-session",
        "surface": "form",
        "predicates": ["phase", "submit_present"],
        "symbols": {
            "form": {
                "kind": "target_reference",
                "target_reference": "form-handle",
                "identity_predicate": "phase",
                "dependencies": ["phase", "submit_present"],
            }
        },
        "actions": {
            "enter": {
                "target_symbol": "form",
                "operation": "enter_value",
                "expected_effect": {"phase": 1},
            },
            "submit": {
                "target_symbol": "form",
                "operation": "submit",
                "expected_effect": {"phase": 2},
            },
        },
        "method": {
            "name": "two-step-form",
            "version": "1",
            "initial_state": "editing",
            "max_transitions": 2,
            "max_runtime_ms": 1000,
            "states": {
                "editing": {"branches": [{
                    "when": {"phase": 0},
                    "outcome": "action",
                    "action": "enter",
                    "next_state": "ready",
                    "reason": None,
                }]},
                "ready": {"branches": [{
                    "when": {"phase": 1, "submit_present": True},
                    "outcome": "action",
                    "action": "submit",
                    "next_state": "submitted",
                    "reason": None,
                }]},
                "submitted": {"branches": [{
                    "when": {"phase": 2},
                    "outcome": "complete",
                    "action": None,
                    "next_state": None,
                    "reason": None,
                }]},
            },
        },
    }


class CompositionDriver:
    def __init__(self, changed=False):
        self.changed = changed
        self.clock = Clock()
        self.actions = []
        self.admissions = []
        self.local_effect_checks = []
        self.outer_effect_checks = []
        self.runtime_receipts = []
        self.model_calls = []

    def model_result(self, output, call_id):
        self.model_calls.append(call_id)
        return {
            "call_id": call_id,
            "thread_id": "thread-" + call_id,
            "output": output,
            "usage": copy.deepcopy(USAGE),
            "requested_model": "synthetic-model",
            "requested_effort": "low",
            "cost": None,
            "visible_images_submitted": 1,
            "wait_ns": 1000,
        }

    def run(self):
        target = {"target_reference": "form-handle", "surface": "form"}
        spec = {
            "target": "synthetic form submission",
            "route": "cold",
            "coarse_origin": "model_produced",
            "provided_coarse": None,
            "cached_target": None,
            "local_repair_on": [],
            "repair_on": [],
            "session_id": "synthetic-composed-session",
        }

        def observe_source(_payload):
            return {"evidence_ref": "fixture://source", "evidence_digest": "source-digest"}

        def coarse_model(_payload):
            return self.model_result(
                {"status": "candidate", "candidate": "form"}, "coarse-01")

        def acquire_anchor(_payload):
            return {"image_ref": "fixture://anchor", "surface": "form"}

        def anchor_model(_payload):
            return self.model_result(
                {"status": "target_reference", "target": target}, "anchor-01")

        def execute(_payload):
            sequence = [0]

            def observe(request):
                sequence[0] += 1
                phase = sequence[0] - 1
                submit_present = True
                if self.changed and sequence[0] == 2:
                    # The first effect remains verified, while the later target
                    # disappears before its branch can be admitted.
                    phase = 1
                    submit_present = False
                return {
                    "sequence": sequence[0],
                    "captured_ns": self.clock(),
                    "surface": "form",
                    "predicates": {
                        "phase": phase,
                        "submit_present": submit_present,
                    },
                    "evidence_ref": f"fixture://frame-{sequence[0]}",
                    "evidence_digest": f"frame-digest-{sequence[0]}",
                }

            def admit(request):
                self.admissions.append(request["action"])
                return {
                    "eligible": True,
                    "status": "revalidated",
                    "authorization": f"one-use-{len(self.admissions)}",
                    "expected_sequence": request["observation"]["sequence"],
                    "valid_until_ns": 1_000_000_000,
                }

            def local_execute(request):
                self.actions.append(request["operation"])
                return {
                    "status": "completed",
                    "action_id": f"action-{len(self.actions)}",
                    "effect_ref": f"fixture://effect-{len(self.actions)}",
                    "release": {
                        "verified": True,
                        "keys_down": [],
                        "buttons_down": [],
                    },
                }

            def local_effect(request):
                self.local_effect_checks.append(request["action"])
                return {
                    "status": "succeeded",
                    "evidence_ref": request["observation"]["evidence_ref"],
                }

            journal = []
            runtime_receipt = run_compiled(compiled_interface(), {
                "observe": observe,
                "admit": admit,
                "execute": local_execute,
                "verify_effect": local_effect,
                "cancelled": lambda: False,
                "journal": journal.append,
            }, clock=self.clock)
            self.runtime_receipts.append(runtime_receipt)
            if runtime_receipt["outcome"] == "TASK_SUCCEEDED":
                return {"status": "completed"}
            if runtime_receipt["outcome"] == "SAFE_YIELD":
                return {
                    "status": "safe_yield",
                    "reason": runtime_receipt["reason"],
                    "completed_actions": runtime_receipt["completed_transitions"],
                }
            return {
                "status": "failed",
            }

        def verify_task_effect(_payload):
            self.outer_effect_checks.append("independent-score")
            succeeded = self.actions == ["enter_value", "submit"]
            return {
                "status": "succeeded" if succeeded else "failed",
                "evidence_ref": "fixture://independent-task-score",
                "evidence_digest": "synthetic-score-digest",
                "effect_scope": "form-submit",
            }

        adapters = {
            "observe_source": observe_source,
            "coarse_model": coarse_model,
            "acquire_anchor": acquire_anchor,
            "anchor_model": anchor_model,
            "final_revalidate": lambda _payload: {"status": "revalidated"},
            "execute": execute,
            "verify_effect": verify_task_effect,
        }
        return run_caller(spec, adapters, clock=self.clock), spec, target


class AdaptiveCallerCompiledGuiCompositionTest(unittest.TestCase):
    def test_cold_accounting_composes_with_evidence_selected_local_continuation(self):
        driver = CompositionDriver()
        result, _spec, target = driver.run()

        self.assertEqual(result["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(result["selected_target"], target)
        self.assertEqual(result["comparison"]["class"], "full_cold")
        self.assertEqual(result["accounting"]["attempted_calls"], 2)
        self.assertEqual(result["accounting"]["completed_calls"], 2)
        self.assertEqual(result["accounting"]["usage_totals"], {
            "input_tokens": 200,
            "cached_input_tokens": 40,
            "cache_write_input_tokens": 0,
            "output_tokens": 24,
            "reasoning_output_tokens": 6,
        })
        runtime_receipt, = driver.runtime_receipts
        self.assertEqual(runtime_receipt["outcome"], "TASK_SUCCEEDED")
        self.assertEqual(runtime_receipt["completed_transitions"], 2)
        self.assertEqual(runtime_receipt["frontier_model_resumptions"], 0)
        self.assertEqual(driver.actions, ["enter_value", "submit"])
        self.assertEqual(driver.admissions, ["enter", "submit"])
        self.assertEqual(driver.outer_effect_checks, ["independent-score"])
        self.assertEqual(result["effect_receipt"]["effect_scope"], "form-submit")

    def test_changed_intermediate_evidence_stops_before_second_admission(self):
        driver = CompositionDriver(changed=True)
        result, _spec, _target = driver.run()

        self.assertEqual(result["outcome"], "EXECUTION_INCOMPLETE")
        self.assertEqual(result["reason"], "unknown_state")
        self.assertEqual(result["delivery"], "confirmed_partial")
        self.assertEqual(result["accounting"]["attempted_calls"], 2)
        runtime_receipt, = driver.runtime_receipts
        self.assertEqual(runtime_receipt["outcome"], "SAFE_YIELD")
        self.assertEqual(runtime_receipt["reason"], "unknown_state")
        self.assertEqual(runtime_receipt["completed_transitions"], 1)
        self.assertEqual(driver.actions, ["enter_value"])
        self.assertEqual(driver.admissions, ["enter"])
        self.assertEqual(driver.outer_effect_checks, [])
        self.assertIsNone(result["task_effect"])


if __name__ == "__main__":
    unittest.main()
