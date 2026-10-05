import time
import unittest

import compiled_gui


def make_interface():
    return {
        "format": "compiled-gui-interface-v1",
        "interface_id": "journal-write-regression",
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
            "max_runtime_ms": 5000,
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


class CompiledJournalExceptionTests(unittest.TestCase):
    def test_terminal_journal_failure_returns_prefix_and_stops(self):
        counts = {"observe": 0, "execute": 0, "verify": 0}
        events = []

        def observe(_request):
            counts["observe"] += 1
            n = counts["observe"]
            return {
                "sequence": n,
                "captured_ns": time.perf_counter_ns(),
                "surface": "test-surface",
                "predicates": {"ready": True, "done": n > 1},
                "evidence_ref": f"frame-{n}",
                "evidence_digest": f"digest-{n}",
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

        def verify_effect(_request):
            counts["verify"] += 1
            return {"status": "succeeded", "evidence_ref": "effect-proof"}

        def journal(event):
            events.append(event)
            if event["event"] == "action_terminal":
                raise OSError("injected journal failure after input")

        receipt = compiled_gui.run(make_interface(), {
            "observe": observe,
            "admit": admit,
            "execute": execute,
            "verify_effect": verify_effect,
            "cancelled": lambda: False,
            "journal": journal,
        })

        self.assertEqual((receipt["outcome"], receipt["reason"]),
                         ("RUNTIME_FAILED", "execution_failed"))
        self.assertEqual(counts, {"observe": 1, "execute": 1, "verify": 0})
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertTrue(receipt["transitions"][0]["release_verified"])
        self.assertEqual(receipt["pending_effect"], {
            "action": "click_save",
            "expected_effect": {"done": True},
            "effect_ref": "effect-1",
        })
        critical = receipt["critical_events"]
        self.assertEqual([event["event"] for event in critical][-3:], [
            "action_terminal", "journal_write_failed", "runtime_finished"
        ])
        self.assertEqual(critical[-2]["error_type"], "OSError")
        self.assertEqual(critical[-1]["outcome"], "RUNTIME_FAILED")
        self.assertEqual(events[-1]["event"], "action_terminal")


if __name__ == "__main__":
    unittest.main()
