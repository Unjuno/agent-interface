import time
import unittest

from runtime.cli_v1.supervised_win32_compiled import run_public_compiled


class SupervisedWin32CompiledCallerTests(unittest.TestCase):
    def test_generation_change_from_standard_observation_stops_compiled_suffix(self):
        generation = "a" * 64
        observations = 0
        dispatches = []
        interface = {
            "format": "compiled-gui-interface-v1",
            "interface_id": "public-win32-generation-check",
            "session_scope": "test-session",
            "surface": "fixture-window",
            "predicates": ["ready", "saved"],
            "symbols": {"fixture": {"kind": "target_reference",
                "target_reference": "fixture", "identity_predicate": "ready",
                "dependencies": ["ready"]}},
            "actions": {"save": {"target_symbol": "fixture",
                "operation": "save", "expected_effect": {"saved": True}}},
            "method": {"name": "save-once", "version": "1",
                "initial_state": "before", "max_transitions": 1,
                "max_runtime_ms": 1000,
                "states": {
                    "before": {"branches": [{"when": {"ready": True,
                        "saved": False}, "outcome": "action", "action": "save",
                        "next_state": "after", "reason": None}]},
                    "after": {"branches": [{"when": {"saved": True},
                        "outcome": "complete", "action": None,
                        "next_state": None, "reason": None}]}}},
        }
        program = {"schema": "agent-interface/program-v1",
            "program_id": "template",
            "source": {"observation_seq": 1, "binding_revision": 7,
                "target_generations": {"fixture": generation}},
            "authority": {"lease_id": "template-lease",
                "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"}]}

        def observe(_target, _frame, _region):
            nonlocal observations, generation
            observations += 1
            if observations == 2:
                generation = "b" * 64
            return {"status": "returned", "target": "fixture",
                "target_generation": generation,
                "target_generation_consistency": "matched",
                "observation": {"capture_started_ns": time.monotonic_ns()},
                "observation_id": f"observe-{observations}"}

        def dispatch(program, sequence, binding_revision):
            dispatches.append((program, sequence, binding_revision))
            return {"status": "completed", "action_id": "action-1",
                "effect_ref": "effect-1", "input_dispatched": True,
                "release": {"verified": True, "keys_down": [],
                    "buttons_down": []}}

        receipt = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1],
            observe=observe, dispatch=dispatch,
            perceive=lambda _row, _reply: {"ready": True,
                "saved": observations > 1},
            verify_effect=lambda _request, _row, _reply: {
                "status": "succeeded", "evidence_ref": "effect-observation"},
            cancelled=lambda: False)

        self.assertEqual(receipt["outcome"], "SAFE_YIELD", receipt)
        self.assertEqual(receipt["reason"], "association_changed")
        self.assertEqual(len(dispatches), 1)
        sent_program, sequence, binding_revision = dispatches[0]
        self.assertEqual(sent_program["source"]["target_generations"],
            {"fixture": "a" * 64})
        self.assertEqual(sent_program["source"]["observation_seq"], sequence)
        self.assertEqual(binding_revision, 7)
        self.assertFalse(receipt.get("task_success", False))


if __name__ == "__main__":
    unittest.main()
