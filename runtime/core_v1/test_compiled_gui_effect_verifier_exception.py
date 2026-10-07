import time
import unittest

import compiled_gui


def interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "effect-callback-regression",
        "session_scope": "test-session",
        "surface": "test-surface",
        "predicates": ["ready", "done"],
        "symbols": {
            "save": {
                "kind": "target_reference",
                "target_reference": "target-save",
                "identity_predicate": "ready",
                "dependencies": ["ready"],
            }
        },
        "actions": {
            "click_save": {
                "target_symbol": "save",
                "operation": "click",
                "expected_effect": {"done": True},
            }
        },
        "method": {
            "name": "one-action",
            "version": "1",
            "initial_state": "before",
            "max_transitions": 2,
            "max_runtime_ms": 5_000,
            "states": {
                "before": {
                    "branches": [{
                        "when": {"ready": True, "done": False},
                        "outcome": "action",
                        "action": "click_save",
                        "next_state": "after",
                        "reason": None,
                    }]
                },
                "after": {
                    "branches": [{
                        "when": {"done": True},
                        "outcome": "complete",
                        "action": None,
                        "next_state": None,
                        "reason": None,
                    }]
                },
            },
        },
    }


class CompiledEffectVerifierExceptionTests(unittest.TestCase):
    def run_case(self, verifier):
        counts = {"observe": 0, "execute": 0}
        events = []

        def observe(_request):
            counts["observe"] += 1
            return {
                "sequence": counts["observe"],
                "captured_ns": time.perf_counter_ns(),
                "surface": "test-surface",
                "predicates": {"ready": True, "done": counts["observe"] > 1},
                "evidence_ref": f"frame-{counts['observe']}",
                "evidence_digest": f"digest-{counts['observe']}",
            }

        def admit(request):
            return {
                "eligible": True,
                "status": "revalidated",
                "authorization": "one-use-auth",
                "expected_sequence": request["observation"]["sequence"],
                "valid_until_ns": time.perf_counter_ns() + 1_000_000_000,
            }

        def execute(_request):
            counts["execute"] += 1
            return {
                "status": "completed",
                "action_id": "action-1",
                "effect_ref": "effect-1",
                "release": {"verified": True, "keys_down": [], "buttons_down": []},
            }

        receipt = compiled_gui.run(interface(), {
            "observe": observe,
            "admit": admit,
            "execute": execute,
            "verify_effect": verifier,
            "cancelled": lambda: False,
            "journal": events.append,
        })
        return receipt, counts, events

    def test_verifier_exception_returns_typed_receipt_and_keeps_prefix(self):
        def fail(_request):
            raise RuntimeError("injected verifier failure")

        receipt, counts, events = self.run_case(fail)
        self.assertEqual(counts["execute"], 1)
        self.assertEqual((receipt["outcome"], receipt["reason"]),
                         ("RUNTIME_FAILED", "effect_unavailable"))
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertTrue(receipt["transitions"][0]["release_verified"])
        self.assertEqual(receipt["pending_effect"], {
            "action": "click_save",
            "expected_effect": {"done": True},
            "effect_ref": "effect-1",
        })
        failed = [e for e in receipt["critical_events"]
                  if e["event"] == "effect_verification_failed"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["error_type"], "RuntimeError")
        self.assertEqual(receipt["critical_events"][-1]["event"], "runtime_finished")
        self.assertEqual(receipt["critical_events"][-1]["outcome"], "RUNTIME_FAILED")
        self.assertEqual(events[-1]["event"], "runtime_finished")

    def test_successful_verifier_control_still_completes(self):
        def succeed(_request):
            return {"status": "succeeded", "evidence_ref": "effect-proof"}

        receipt, counts, _events = self.run_case(succeed)
        self.assertEqual(counts["execute"], 1)
        self.assertEqual((receipt["outcome"], receipt["reason"]),
                         ("TASK_SUCCEEDED", "method_complete"))
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertIsNone(receipt["pending_effect"])


if __name__ == "__main__":
    unittest.main()
