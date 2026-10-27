import time
import unittest
from runtime.cli_v1.supervised_win32_compiled import run_public_compiled

class DispatchCompositionTests(unittest.TestCase):
    def test_conflicting_delivery_stops_before_effect_oracle(self):
        generation = "b" * 64
        dispatch_id = "a" * 32
        operation_id = "c" * 32
        observations = []
        dispatches = []
        resolutions = []
        task_calls = []
        interface = {
            "format": "compiled-gui-interface-v1",
            "interface_id": "pending-public-win32-dispatch",
            "session_scope": "test-session",
            "surface": "fixture-window",
            "predicates": ["ready", "moved"],
            "symbols": {"fixture": {"kind": "target_reference",
                "target_reference": "fixture", "identity_predicate": "ready",
                "dependencies": ["ready"]}},
            "actions": {"move": {"target_symbol": "fixture",
                "operation": "move", "expected_effect": {"moved": True}}},
            "method": {"name": "move-once", "version": "1",
                "initial_state": "before", "max_transitions": 1,
                "max_runtime_ms": 1000,
                "states": {
                    "before": {"branches": [{"when": {"ready": True},
                        "outcome": "action", "action": "move",
                        "next_state": "after", "reason": None}]},
                    "after": {"branches": [{"when": {"moved": True},
                        "outcome": "complete", "action": None,
                        "next_state": None, "reason": None}]}}},
        }
        program = {"schema": "agent-interface/program-v1",
            "program_id": "template",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": generation}},
            "authority": {"lease_id": "template-lease",
                "expires_at_ns": time.monotonic_ns() + 5_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_state", "key": "W", "down": True,
                    "encoding": "scan_code"},
                {"op": "key_state", "key": "W", "down": False,
                    "encoding": "scan_code"},
                {"op": "release_all"}]}

        def observe(target, frame, region):
            observations.append((target, frame, region))
            index = len(observations)
            return {"status": "returned", "call_id": f"{index:032x}",
                "target": target, "target_generation": generation,
                "target_generation_consistency": "matched",
                "observation": {"target": target,
                    "capture_started_ns": time.monotonic_ns()},
                "observation_id": f"observation-{index}",
                "predicates": {"ready": True,
                    "moved": index > 1}}

        def dispatch(_program, _sequence, _binding_revision):
            dispatches.append(True)
            return {"status": "pending", "call_id": dispatch_id,
                "operation_invoked": True, "input_dispatched": None,
                "release_confirmed": False, "replay_allowed": False}

        def resolve_pending(call_id, pending_reply):
            resolutions.append((call_id, pending_reply["status"]))
            return {"call_id": call_id,
                "action": {"operation_id": operation_id,
                    "target_generation": generation, "status": "completed",
                    "input_dispatched": True, "release_confirmed": True,
                    "completion_custody": {"release_confirmed": True,
                        "completion_readback_outcome": "verified"},
                    "result": {"status": "completed",
                        "input_dispatched": False,
                        "release_confirmed": True}}}

        def verify_task(call_id):
            task_calls.append(call_id)
            requested = time.monotonic_ns() - 2_000_000
            observed = requested + 1_000_000
            accepted = observed + 1_000_000
            receipt = {"call_id": call_id, "operation_id": operation_id,
                "target_generation": generation, "oracle_id": "e" * 32,
                "outcome": "success", "observed_monotonic_ns": observed,
                "evidence_ref": "pixel-proof"}
            return {"status": "verified", "call_id": call_id,
                "task_success": True, "operation_invoked": False,
                "input_dispatched": False, "replay_allowed": False,
                "scope": "supervised_win32",
                "task_effect": {"status": "verified", "task_success": True,
                    "receipt": receipt, "requested_monotonic_ns": requested,
                    "receipt_received_monotonic_ns": accepted}}

        result = run_public_compiled(interface, {"move": program},
            target="fixture", current_binding_revision=1,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            resolve_pending=resolve_pending,
            perceive=lambda _report, reply: reply["predicates"],
            verify_effect=lambda _request, _report, _reply: {
                "status": "succeeded", "evidence_ref": "pixel-proof"},
            verify_task=verify_task, cancelled=lambda: False)

        self.assertEqual(result["outcome"], "SAFE_YIELD", result)
        self.assertEqual(dispatches, [True])
        self.assertEqual(resolutions, [(dispatch_id, "pending")])
        self.assertEqual(len(observations), 1)
        self.assertEqual(task_calls, [])
        self.assertIsNone(result["task_success"])
        self.assertIsNone(result["task_verification"])
        dispatch_evidence = result["standard_target_evidence"][1]
        self.assertEqual(dispatch_evidence["status"], "uncertain")
        self.assertIsNone(dispatch_evidence["input_dispatched"])
        self.assertTrue(dispatch_evidence["release_verified"])
