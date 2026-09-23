import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
import map01_overlap_controller_v38 as controller
from test_map01_overlap_controller_v37 import action, initial_receipt, signal, BINDING
from running_action_guard_v3 import RunningActionGuardV3
from executor_v11 import program_sha256


class Stream:
    def __init__(self): self.writes = []
    def write(self, value): self.writes.append(value)
    def flush(self): pass


class Process:
    def __init__(self): self.stdin = Stream()


class Map01OverlapControllerV38Tests(unittest.TestCase):
    def test_cancel_consumes_physical_release_before_terminal(self):
        candidate = action()
        ready = controller.prepare_action_admission(
            initial_receipt(), candidate, candidate["action_validity"][0],
            signal("health", 85, 1, 100), signal("ammo", 47, 1, 100),
            signal("health", 85, 2, 200), signal("ammo", 47, 2, 200), 201)
        guard = RunningActionGuardV3(
            candidate, ready, controller.compile_commands,
            "map01_overlap_controller_v38.compile_commands")
        steps = controller.compile_commands(candidate["commands"])
        command = {"op": "submit", "id": "p1", "expected_sequence": 2,
                   "valid_until_ns": 1000, "steps": steps}
        guard.admit_program(
            {"role": "primary", "semantic_commands": candidate["commands"],
             "command_indices": [0], "contingency_after": None,
             "compiled_steps": steps},
            {"command": command, "sent_ns": 202},
            {"event": "accepted", "id": "p1", "steps": 1,
             "program_sha256": program_sha256(steps),
             "intent_token": "lease-p1", "accepted_ns": 203})
        guard.check_current({"format": "action-admission-snapshot-v1",
            "sequence": 3, "capture_ns": 300, "binding": BINDING,
            "signals": {"health": {"status": "observed", "value": 70},
                        "ammo": {"status": "observed", "value": 46}}}, 301)
        rows = iter([
            {"event": "cancel_requested", "id": "p1", "matched": True,
             "requested_ns": 302, "emit_ns": 303},
            {"event": "input_released", "id": "p1", "intent_token": "lease-p1",
             "owner_release": {"event": "owner_release", "reason": "cancelled",
                "verified": True, "keys_down": [], "buttons_down": [],
                "verified_ns": 304, "valid_until_ns": 1000},
             "published_ns": 305, "program_terminal_pending": True,
             "grants_input_authority": False, "emit_ns": 306},
            {"event": "terminal", "id": "p1", "status": "cancelled",
             "terminal_ns": 310, "release": {"verified": True,
             "keys_down": [], "buttons_down": [], "verified_ns": 309}}])
        seen = []
        def wait(predicate):
            row = next(rows); self.assertTrue(predicate(row)); seen.append(row["event"]); return row
        process = Process()
        cancel, released, pending, terminal, closed = controller.cancel_invalidated_action(
            process, wait, "p1", guard)
        self.assertEqual(seen, ["cancel_requested", "input_released", "terminal"])
        self.assertEqual(json.loads(process.stdin.writes[0]), {"op": "cancel", "id": "p1"})
        self.assertTrue(pending["physical_release_verified"])
        self.assertTrue(pending["program_terminal_pending"])
        self.assertEqual(pending["state"], "REVOKED_INPUT_RELEASED_AWAITING_TERMINAL")
        self.assertEqual(terminal["status"], "cancelled")
        self.assertFalse(closed["program_terminal_pending"])
        self.assertEqual(closed["state"], "REVOKED_ACTION_NOT_CURRENT")


if __name__ == "__main__": unittest.main()
