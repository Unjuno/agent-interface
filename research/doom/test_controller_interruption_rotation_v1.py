import io
import sys
import unittest
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import map01_overlap_controller_v39 as controller


class ControllerInterruptionRotationTests(unittest.TestCase):
    def test_matching_interruption_can_use_bounded_rotation_and_fresh_source(self):
        terminal = {"event": "terminal", "id": "plan-interrupted",
                    "status": "needs_decision", "input_owner_generation": 4,
                    "input_owner_id": "owner-4",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": [],
                                "target_process_identity_reader": {"retired": True}},
                    "interruption": {"intent_token": "intent-x", "record": {
                        "event": "owner_release", "intent_token": "intent-x",
                        "reason": "target_generation_invalidated", "verified": True,
                        "keys_down": [], "buttons_down": [], "keys_unknown": [],
                        "key_state_errors": [],
                        "target_process_identity_reader": {"retired": True},
                        "key_release_attempts": {"113": {"verified": True,
                            "attempts": [{"attempt": 1,
                                "keyrelease_started_ns": 10, "sync_returned_ns": 11,
                                "keymap_sampled_ns": 12,
                                "server_key_down_before": True,
                                "server_key_down_after": False}]}}}}}
        receipt = {"event": "input_owner_generation", "terminal_id": terminal["id"],
                   "generation": 5, "previous_generation": 4,
                   "previous_owner_id": "owner-4", "owner_id": "owner-5",
                   "source_invalidated": True, "grants_input_authority": False}
        observation = {"event": "observation", "id": "owner-generation-source-5-1",
                       "input_owner_generation": 5, "sequence": 42,
                       "pointer_binding": {"surface": 17},
                       "target_process_identity": {"sequence": 42, "surface": 17,
                                                    "digest": "d" * 64}}
        refreshed = {"event": "input_owner_source_refreshed", "terminal_id": terminal["id"],
                     "generation": 5, "owner_id": "owner-5",
                     "observation_id": observation["id"], "sequence": 42,
                     "attempt": 1, "surface": 17, "digest": "d" * 64,
                     "source_invalidated": False, "grants_input_authority": False}
        events = [receipt, observation, refreshed]
        def wait(predicate, timeout=40):
            return next(row for row in events if predicate(row))
        process = Namespace(stdin=io.StringIO())
        result = controller.rotate_retired_owner_after_cancel(
            process, wait, terminal, minimum_sequence=41,
            expected_intent_token="intent-x")
        self.assertEqual(result["generation"], 5)
        self.assertEqual(result["source_observation"], observation)
        self.assertIn('"op": "rotate_input_owner"', process.stdin.getvalue())

    def test_mismatched_intent_refuses_before_rotation_command(self):
        process = Namespace(stdin=io.StringIO())
        terminal = {"event": "terminal", "id": "plan-interrupted",
                    "status": "needs_decision", "input_owner_generation": 4,
                    "input_owner_id": "owner-4",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": [],
                                "target_process_identity_reader": {"retired": True}},
                    "interruption": {
                        "intent_token": "intent-x", "record": {}}}
        with self.assertRaises(ValueError):
            controller.rotate_retired_owner_after_cancel(
                process, lambda _predicate: None, terminal, minimum_sequence=1,
                expected_intent_token="intent-y")
        self.assertEqual(process.stdin.getvalue(), "")

    def test_composed_recovery_revokes_first_then_requires_newer_source(self):
        terminal = {"event": "terminal", "id": "plan-interrupted",
                    "status": "needs_decision", "input_owner_generation": 4,
                    "input_owner_id": "owner-4",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": [],
                                "target_process_identity_reader": {"retired": True}},
                    "interruption": {"intent_token": "intent-x", "record": {
                        "event": "owner_release", "intent_token": "intent-x",
                        "reason": "target_generation_invalidated", "verified": True,
                        "keys_down": [], "buttons_down": [], "keys_unknown": [],
                        "key_state_errors": [],
                        "target_process_identity_reader": {"retired": True},
                        "key_release_attempts": {"113": {"verified": True,
                            "attempts": [{"attempt": 1, "keyrelease_started_ns": 10,
                                "sync_returned_ns": 11, "keymap_sampled_ns": 12,
                                "server_key_down_before": True,
                                "server_key_down_after": False}]}}}}}
        order = []
        class Stdin:
            def write(self, payload): order.append("rotation_or_refresh")
            def flush(self): pass
        class Guard:
            def record_interrupted_terminal(self, row):
                order.append("guard_revoked")
                return {"state": "REVOKED_ACTION_NOT_CURRENT",
                        "current_input_authority": False,
                        "physical_input_may_be_down": False,
                        "requires_new_decision": True}
        receipt = {"event": "input_owner_generation", "terminal_id": terminal["id"],
                   "generation": 5, "previous_generation": 4,
                   "previous_owner_id": "owner-4", "owner_id": "owner-5",
                   "source_invalidated": True, "grants_input_authority": False}
        observation = {"event": "observation", "id": "owner-generation-source-5-1",
                       "input_owner_generation": 5, "sequence": 42,
                       "pointer_binding": {"surface": 17},
                       "target_process_identity": {"sequence": 42, "surface": 17,
                                                    "digest": "d" * 64}}
        refreshed = {"event": "input_owner_source_refreshed", "terminal_id": terminal["id"],
                     "generation": 5, "owner_id": "owner-5",
                     "observation_id": observation["id"], "sequence": 42,
                     "attempt": 1, "surface": 17, "digest": "d" * 64,
                     "source_invalidated": False, "grants_input_authority": False}
        rows = [receipt, observation, refreshed]
        def wait(predicate, timeout=40):
            return next(row for row in rows if predicate(row))
        guard_receipt, rotation = controller.recover_owner_interruption(
            Namespace(stdin=Stdin()), wait, terminal, Guard(),
            expected_intent_token="intent-x", minimum_sequence=41)
        self.assertEqual(order[0], "guard_revoked")
        self.assertEqual(order[1], "rotation_or_refresh")
        self.assertEqual(guard_receipt["state"], "REVOKED_ACTION_NOT_CURRENT")
        self.assertEqual(rotation["source_observation"], observation)

    def test_composed_recovery_keeps_action_revoked_if_rotation_fails(self):
        terminal = {"event": "terminal", "id": "plan-interrupted",
                    "status": "needs_decision", "input_owner_generation": 4,
                    "input_owner_id": "owner-4",
                    "release": {"verified": True, "keys_down": [],
                                "buttons_down": [], "keys_unknown": [],
                                "key_state_errors": [],
                                "target_process_identity_reader": {"retired": True}},
                    "interruption": {
                        "intent_token": "intent-x", "record": {
                            "event": "owner_release", "intent_token": "intent-x",
                            "reason": "target_generation_invalidated", "verified": True,
                            "keys_down": [], "buttons_down": [], "keys_unknown": [],
                            "key_state_errors": [],
                            "target_process_identity_reader": {"retired": True},
                            "key_release_attempts": {"113": {"verified": True,
                                "attempts": [{"attempt": 1, "keyrelease_started_ns": 10,
                                    "sync_returned_ns": 11, "keymap_sampled_ns": 12,
                                    "server_key_down_before": True,
                                    "server_key_down_after": False}]}}}}}
        order = []
        class Guard:
            def record_interrupted_terminal(self, row):
                order.append("revoked")
                return {"state": "REVOKED_ACTION_NOT_CURRENT",
                        "current_input_authority": False,
                        "physical_input_may_be_down": False,
                        "requires_new_decision": True}
        rejected = {"event": "rejected", "id": terminal["id"],
                    "terminal_id": terminal["id"], "operation": "rotate_input_owner",
                    "reason": "refused"}
        with self.assertRaises(RuntimeError):
            controller.recover_owner_interruption(
                Namespace(stdin=type("Stdin", (), {"write": lambda *_: None,
                                                    "flush": lambda *_: None})()),
                lambda predicate, timeout=40: rejected if predicate(rejected) else None,
                terminal, Guard(), expected_intent_token="intent-x", minimum_sequence=1)
        self.assertEqual(order, ["revoked"])


if __name__ == "__main__":
    unittest.main()
