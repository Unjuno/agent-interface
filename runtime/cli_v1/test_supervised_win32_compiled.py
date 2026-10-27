import time
import unittest

from runtime.cli_v1.supervised_win32_compiled import (
    _terminal, run_public_compiled)


class SupervisedWin32CompiledCallerTests(unittest.TestCase):
    def test_retrieved_dispatch_requires_exact_call_and_generation(self):
        call_id = "a" * 32
        generation = "b" * 64
        retrieved = {"call_id": call_id,
            # interface_results describes its own read as no input; the
            # nested action retains the original dispatch's delivery state.
            "input_dispatched": False,
            "action": {"operation_id": "c" * 32,
                "target_generation": generation, "status": "completed",
                "input_dispatched": True, "release_confirmed": True,
                "completion_custody": {"release_confirmed": True,
                    "completion_readback_outcome": "verified"},
                "result": {"status": "completed",
                    "input_dispatched": True, "release_confirmed": True}}}

        accepted = _terminal(retrieved, "move", expected_call_id=call_id,
            expected_generation=generation)
        self.assertEqual(accepted["status"], "completed")
        self.assertIs(accepted["release"]["verified"], True)
        self.assertIs(accepted["input_dispatched"], True)

        # The public interface_results action keeps the canonical release
        # confirmation on the action/custody row. Its nested runtime result
        # records the verified release receipt but omits a redundant boolean.
        public_result_shape = {**retrieved, "action": {
            **retrieved["action"], "result": {"status": "completed",
                "execution": {"releases": [{"verified": True,
                    "keys_down": [], "buttons_down": []}]}}}}
        public_result_terminal = _terminal(public_result_shape, "move",
            expected_call_id=call_id, expected_generation=generation)
        self.assertEqual(public_result_terminal["status"], "completed")
        self.assertIs(public_result_terminal["release"]["verified"], True)

        wrong_call = _terminal(retrieved, "move",
            expected_call_id="d" * 32, expected_generation=generation)
        self.assertEqual(wrong_call["status"], "uncertain")
        self.assertIs(wrong_call["release"]["verified"], False)

        wrong_generation = _terminal(retrieved, "move",
            expected_call_id=call_id, expected_generation="e" * 64)
        self.assertEqual(wrong_generation["status"], "uncertain")
        self.assertIs(wrong_generation["release"]["verified"], False)

        recovered = {**retrieved, "action": {**retrieved["action"],
            "status": "recovered", "result": {"status": "recovered",
                "input_dispatched": True, "release_confirmed": True}}}
        recovered_terminal = _terminal(recovered, "move",
            expected_call_id=call_id, expected_generation=generation)
        self.assertEqual(recovered_terminal["status"], "delivery_uncertain")
        self.assertIs(recovered_terminal["release"]["verified"], True)

    def test_pending_dispatch_joins_same_call_id_readback_before_task_verification(self):
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
                        "input_dispatched": True,
                        "release_confirmed": True}}}

        def verify_task(call_id):
            task_calls.append(call_id)
            requested = time.monotonic_ns() - 2_000_000
            observed = requested + 1_000_000
            accepted = observed + 1_000_000
            receipt = {"call_id": call_id, "operation_id": "d" * 32,
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

        self.assertEqual(result["outcome"], "TASK_SUCCEEDED", result)
        self.assertEqual(dispatches, [True])
        self.assertEqual(resolutions, [(dispatch_id, "pending")])
        self.assertEqual(result["standard_action_call_ids"], [dispatch_id])
        self.assertEqual(result["task_verification"]["action_call_id"], dispatch_id)
        self.assertEqual(task_calls, [dispatch_id])
        dispatch_evidence = result["standard_target_evidence"][1]
        self.assertEqual(dispatch_evidence["call_id"], dispatch_id)
        self.assertEqual(dispatch_evidence["action_id"], operation_id)
        self.assertTrue(dispatch_evidence["release_verified"])

    def test_standard_success_binds_fresh_effect_observation_and_call_receipts(self):
        generation = "c" * 64
        def call_id(number): return f"{number:032x}"
        observation_calls = []
        dispatch_calls = []
        effect_checks = []
        dispatch_completed_ns = None
        interface = {
            "format": "compiled-gui-interface-v1",
            "interface_id": "public-win32-fresh-effect-check",
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
                "max_runtime_ms": 2000,
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

        def observe(target, frame, region):
            index = len(observation_calls) + 1
            observation_call_id = call_id(index)
            observation_calls.append((target, frame, region, observation_call_id))
            return {"status": "returned", "call_id": observation_call_id,
                "target": target, "target_generation": generation,
                "target_generation_consistency": "matched",
                "observation": {"target": target,
                    "capture_started_ns": time.monotonic_ns()},
                "observation_id": f"observation-{index}"}

        def dispatch(sent_program, sequence, binding_revision):
            nonlocal dispatch_completed_ns
            dispatch_completed_ns = time.monotonic_ns()
            action_index = len(dispatch_calls) + 1
            dispatch_calls.append((sent_program, sequence, binding_revision))
            return {"status": "completed", "call_id": call_id(100 + action_index),
                "action_id": f"action-{action_index}",
                "effect_ref": f"effect-{action_index}",
                "input_dispatched": True,
                "release": {"verified": True, "keys_down": [],
                    "buttons_down": []}}

        def verify_effect(request, report, reply):
            effect_checks.append((request, report, reply))
            return {"status": "succeeded", "evidence_ref": "score-observation-2"}

        receipt = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, reply: {"ready": True,
                "saved": int(reply["call_id"], 16) % 2 == 0},
            verify_effect=verify_effect, cancelled=lambda: False)

        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED", receipt)
        self.assertEqual(receipt["completed_transitions"], 1)
        self.assertIsNone(receipt["task_success"])
        self.assertEqual(receipt["standard_observation_call_ids"],
            [call_id(1), call_id(2)])
        self.assertEqual(receipt["standard_action_call_ids"], [call_id(101)])
        evidence = receipt["standard_target_evidence"]
        self.assertEqual([row["kind"] for row in evidence],
            ["observation", "dispatch", "observation"])
        self.assertEqual([row["call_id"] for row in evidence],
            [call_id(1), call_id(101), call_id(2)])
        self.assertTrue(all(row["target_generation"] == generation
            for row in evidence))
        self.assertEqual(receipt["bound_target_generation"], generation)
        self.assertEqual(evidence[0]["target_generation_consistency"], "matched")
        self.assertEqual(evidence[2]["observation_id"], "observation-2")
        self.assertTrue(evidence[0]["compiled_observation_accepted"])
        self.assertTrue(evidence[2]["compiled_observation_accepted"])
        self.assertEqual(evidence[2]["observation_sequence"], 2)
        self.assertEqual(evidence[1]["observation_sequence"], 1)
        self.assertEqual(evidence[1]["binding_revision"], 7)
        self.assertEqual(evidence[1]["action_id"], "action-1")
        self.assertTrue(evidence[1]["release_verified"])
        self.assertEqual(len(observation_calls), 2)
        self.assertEqual(len(dispatch_calls), 1)
        sent_program, sequence, binding_revision = dispatch_calls[0]
        self.assertEqual(sent_program["source"]["target_generations"],
            {"fixture": generation})
        self.assertEqual(sent_program["source"]["observation_seq"], sequence)
        self.assertEqual(binding_revision, 7)
        self.assertEqual(len(effect_checks), 1)
        request, effect_report, effect_reply = effect_checks[0]
        self.assertEqual(request["observation"]["sequence"], 2)
        self.assertGreaterEqual(request["observation"]["captured_ns"],
            dispatch_completed_ns)
        self.assertEqual(effect_report["observation_id"], "observation-2")
        self.assertEqual(effect_reply["call_id"], call_id(2))

        def task_oracle(call_id, verdict=True, echoed_call_id=None,
                        echoed_generation=None, without_receipt=False):
            task_calls.append(call_id)
            status = "unknown" if verdict is None else "verified"
            requested_ns = time.monotonic_ns() - 1_000_000
            observed_ns = requested_ns + 1000
            received_ns = time.monotonic_ns()
            outcome = ("success" if verdict is True else
                "failure" if verdict is False else "unknown")
            oracle_receipt = {"call_id": call_id, "operation_id": "e" * 32,
                "target_generation": echoed_generation or generation,
                "oracle_id": "d" * 32,
                "outcome": outcome, "observed_monotonic_ns": observed_ns,
                "evidence_ref": "oracle-effect-proof"}
            effect = {"status": status, "task_success": verdict,
                "receipt": None if without_receipt else oracle_receipt,
                "requested_monotonic_ns": requested_ns}
            if not without_receipt:
                effect["receipt_received_monotonic_ns"] = received_ns
            else:
                effect["uncertainty"] = "independent_task_oracle_response_timeout"
            return {"status": status,
                "call_id": echoed_call_id or call_id,
                "task_effect": effect,
                "task_success": verdict, "operation_invoked": False,
                "input_dispatched": False, "replay_allowed": False,
                "scope": "supervised_win32"}

        task_calls = []
        passed = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, reply: {"ready": True,
                "saved": int(reply["call_id"], 16) % 2 == 0},
            verify_effect=verify_effect, verify_task=lambda call_id:
                task_oracle(call_id, True), cancelled=lambda: False)
        self.assertEqual(passed["outcome"], "TASK_SUCCEEDED")
        self.assertTrue(passed["task_verification"]["valid"])
        self.assertIs(passed["task_success"], True)
        self.assertEqual(passed["task_verification"]["action_call_id"],
            call_id(102))
        self.assertEqual(passed["task_verification"]["target_generation"], generation)
        task_timing = passed["task_verification"]
        self.assertLessEqual(task_timing["oracle_requested_ns"],
            task_timing["oracle_observed_ns"])
        self.assertLessEqual(task_timing["oracle_observed_ns"],
            task_timing["oracle_receipt_accepted_ns"])
        self.assertEqual(task_timing["oracle_outcome"], "success")
        self.assertEqual(task_timing["effect_evidence_ref"], "oracle-effect-proof")

        failed = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, reply: {"ready": True,
                "saved": int(reply["call_id"], 16) % 2 == 0},
            verify_effect=verify_effect, verify_task=lambda call_id:
                task_oracle(call_id, False), cancelled=lambda: False)
        self.assertEqual(failed["outcome"], "TASK_SUCCEEDED")
        self.assertTrue(failed["task_verification"]["valid"])
        self.assertIs(failed["task_success"], False)

        unknown = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, reply: {"ready": True,
                "saved": int(reply["call_id"], 16) % 2 == 0},
            verify_effect=verify_effect, verify_task=lambda call_id:
                task_oracle(call_id, None), cancelled=lambda: False)
        self.assertTrue(unknown["task_verification"]["valid"])
        self.assertEqual(unknown["task_verification"]["status"], "unknown")
        self.assertIsNone(unknown["task_success"])

        timed_out = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, reply: {"ready": True,
                "saved": int(reply["call_id"], 16) % 2 == 0},
            verify_effect=verify_effect, verify_task=lambda call_id:
                task_oracle(call_id, None, without_receipt=True),
            cancelled=lambda: False)
        self.assertTrue(timed_out["task_verification"]["valid"])
        self.assertEqual(timed_out["task_verification"]["status"], "unknown")
        self.assertIsNone(timed_out["task_verification"]["oracle_observed_ns"])
        self.assertIsNone(timed_out["task_success"])

        mismatched = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, reply: {"ready": True,
                "saved": int(reply["call_id"], 16) % 2 == 0},
            verify_effect=verify_effect, verify_task=lambda call_id:
                task_oracle(call_id, True, "wrong-call-id"), cancelled=lambda: False)
        self.assertFalse(mismatched["task_verification"]["valid"])
        self.assertIsNone(mismatched["task_success"])

        generation_mismatch = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, reply: {"ready": True,
                "saved": int(reply["call_id"], 16) % 2 == 0},
            verify_effect=verify_effect, verify_task=lambda call_id:
                task_oracle(call_id, True, echoed_generation="f" * 64),
            cancelled=lambda: False)
        self.assertFalse(generation_mismatch["task_verification"]["valid"])
        self.assertIsNone(generation_mismatch["task_success"])
        self.assertEqual(task_calls, [call_id(102), call_id(103), call_id(104),
            call_id(105), call_id(106), call_id(107)])

    def test_missing_final_dispatch_call_id_cannot_verify_prior_dispatch(self):
        generation = "a" * 64
        interface = {
            "format": "compiled-gui-interface-v1",
            "interface_id": "final-dispatch-oracle-identity",
            "session_scope": "test-session", "surface": "fixture-window",
            "predicates": ["ready", "saved"],
            "symbols": {"fixture": {"kind": "target_reference",
                "target_reference": "fixture", "identity_predicate": "ready",
                "dependencies": ["ready"]}},
            "actions": {"save": {"target_symbol": "fixture",
                "operation": "save", "expected_effect": {"saved": True}}},
            "method": {"name": "save-twice", "version": "1",
                "initial_state": "before", "max_transitions": 2,
                "max_runtime_ms": 1000,
                "states": {
                    "before": {"branches": [{"when": {"ready": True,
                        "saved": False}, "outcome": "action", "action": "save",
                        "next_state": "middle", "reason": None}]},
                    "middle": {"branches": [{"when": {"ready": True,
                        "saved": True}, "outcome": "action", "action": "save",
                        "next_state": "after", "reason": None}]},
                    "after": {"branches": [{"when": {"saved": True},
                        "outcome": "complete", "action": None,
                        "next_state": None, "reason": None}]}}},
        }
        program = {"schema": "agent-interface/program-v1",
            "program_id": "two-dispatch-template",
            "source": {"observation_seq": 1, "binding_revision": 1,
                "target_generations": {"fixture": generation}},
            "authority": {"lease_id": "two-dispatch-lease",
                "expires_at_ns": time.monotonic_ns() + 10_000_000_000},
            "terminal": {"release_all_required": True},
            "ops": [{"op": "focus", "target": "fixture"},
                {"op": "key_chord", "keys": ["CTRL", "S"]},
                {"op": "release_all"}]}
        observations = 0
        dispatches = []
        oracle_calls = []

        def observe(target, frame, region):
            nonlocal observations
            observations += 1
            call_id = f"{observations:032x}"
            return {"status": "returned", "call_id": call_id,
                "target": target, "target_generation": generation,
                "target_generation_consistency": "matched",
                "observation": {"target": target,
                    "capture_started_ns": time.monotonic_ns()},
                "observation_id": f"observation-{observations}"}

        def dispatch(_program, _sequence, _binding_revision):
            dispatches.append(len(dispatches) + 1)
            reply = {"status": "completed",
                "action_id": f"action-{dispatches[-1]}",
                "effect_ref": f"effect-{dispatches[-1]}",
                "input_dispatched": True,
                "release": {"verified": True, "keys_down": [],
                    "buttons_down": []}}
            if dispatches[-1] == 1:
                reply["call_id"] = "b" * 32
            return reply

        def verify_task(call_id):
            oracle_calls.append(call_id)
            now = time.monotonic_ns()
            receipt = {"call_id": call_id, "operation_id": "c" * 32,
                "target_generation": generation, "oracle_id": "d" * 32,
                "outcome": "success", "observed_monotonic_ns": now,
                "evidence_ref": "prior-action-effect"}
            return {"status": "verified", "call_id": call_id,
                "task_success": True, "operation_invoked": False,
                "input_dispatched": False, "replay_allowed": False,
                "scope": "supervised_win32",
                "task_effect": {"status": "verified", "task_success": True,
                    "receipt": receipt, "requested_monotonic_ns": now - 1,
                    "receipt_received_monotonic_ns": now + 1}}

        receipt = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=1,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _report, _reply: {"ready": True,
                "saved": observations >= 2},
            verify_effect=lambda _request, _report, _reply: {
                "status": "succeeded", "evidence_ref": "effect"},
            verify_task=verify_task, cancelled=lambda: False)

        self.assertEqual(receipt["outcome"], "TASK_SUCCEEDED", receipt)
        self.assertEqual(receipt["completed_transitions"], 2)
        self.assertEqual(dispatches, [1, 2])
        self.assertIsNone(receipt["task_success"])
        self.assertIsNone(receipt["task_verification"])
        self.assertEqual(oracle_calls, [])

    def test_generation_change_from_standard_observation_stops_compiled_suffix(self):
        generation = "a" * 64
        observations = 0
        dispatches = []
        forced_generation = None
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
            if observations == 1 and forced_generation is not None:
                generation = forced_generation
            elif observations == 2:
                generation = "b" * 64
            return {"status": "returned",
                "target_generation": generation,
                "target_generation_consistency": "matched",
                "observation": {"target": "fixture",
                    "capture_started_ns": time.monotonic_ns()},
                "observation_id": f"observe-{observations}"}

        def dispatch(program, sequence, binding_revision):
            dispatches.append((program, sequence, binding_revision))
            return {"status": "completed", "action_id": "action-1",
                "effect_ref": "effect-1", "input_dispatched": True,
                "release": {"verified": True, "keys_down": [],
                    "buttons_down": []}}

        grounded_generation = generation
        forced_generation = "b" * 64
        after_model_wait = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1], observe=observe, dispatch=dispatch,
            perceive=lambda _row, _reply: {"ready": True, "saved": False},
            verify_effect=lambda _request, _row, _reply: {
                "status": "succeeded", "evidence_ref": "unused"},
            expected_generation=grounded_generation, cancelled=lambda: False)
        self.assertEqual(after_model_wait["outcome"], "SAFE_YIELD")
        self.assertEqual(after_model_wait["reason"], "association_changed")
        self.assertEqual(after_model_wait["completed_transitions"], 0)
        self.assertEqual(after_model_wait["observations"], [])
        self.assertIsNone(after_model_wait["bound_target_generation"])
        self.assertEqual(after_model_wait["standard_target_evidence"], [])
        self.assertEqual(observations, 1)
        self.assertEqual(dispatches, [])

        observations = 0
        generation = grounded_generation
        forced_generation = None
        task_oracle_calls = []
        receipt = run_public_compiled(interface, {"save": program},
            target="fixture", current_binding_revision=7,
            region=[0, 0, 1, 1],
            observe=observe, dispatch=dispatch,
            perceive=lambda _row, _reply: {"ready": True,
                "saved": observations > 1},
            verify_effect=lambda _request, _row, _reply: {
                "status": "succeeded", "evidence_ref": "effect-observation"},
            verify_task=lambda call_id: task_oracle_calls.append(call_id),
            cancelled=lambda: False)

        self.assertEqual(receipt["outcome"], "SAFE_YIELD", receipt)
        self.assertEqual(receipt["reason"], "association_changed")
        self.assertEqual(task_oracle_calls, [])
        self.assertEqual(len(dispatches), 1)
        self.assertEqual(receipt["bound_target_generation"], "a" * 64)
        self.assertEqual([row["kind"] for row in receipt["standard_target_evidence"]],
            ["observation", "dispatch"])
        self.assertTrue(all(row["target_generation"] == "a" * 64
            for row in receipt["standard_target_evidence"]))
        sent_program, sequence, binding_revision = dispatches[0]
        self.assertEqual(sent_program["source"]["target_generations"],
            {"fixture": "a" * 64})
        self.assertEqual(sent_program["source"]["observation_seq"], sequence)
        self.assertEqual(binding_revision, 7)
        self.assertFalse(receipt.get("task_success", False))


if __name__ == "__main__":
    unittest.main()
