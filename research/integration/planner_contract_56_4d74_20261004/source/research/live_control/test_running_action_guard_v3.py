import copy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from test_running_action_guard_v2 import (COMMANDS, admission, guard_v2,
    program, snapshot)
from running_action_guard_v3 import RunningActionGuardV3, RELEASED_PENDING


def guard_v3():
    old = guard_v2()
    return RunningActionGuardV3(old.action, old.final_admission,
                                old.compiler, old.compiler_identity)


class RunningActionGuardV3Tests(unittest.TestCase):
    def armed(self):
        guard = guard_v3(); p = program("primary", COMMANDS[:1], [0])
        submit, accepted = admission("p1", p)
        accepted["intent_token"] = "lease-token-1"
        guard.admit_program(p, submit, accepted)
        guard.check_current(snapshot(3, 300, health=20), 301)
        guard.record_cancel_requested({"event": "cancel_requested", "id": "p1",
                                       "matched": True, "requested_ns": 302})
        return guard

    def release(self, **changes):
        row = {"event": "input_released", "id": "p1",
               "intent_token": "lease-token-1",
               "owner_release": {"event": "owner_release", "reason": "cancelled",
                   "verified": True, "keys_down": [], "buttons_down": [],
                   "verified_ns": 303, "valid_until_ns": 1000},
               "published_ns": 304, "program_terminal_pending": True,
               "grants_input_authority": False}
        row.update(changes); return row

    def test_early_release_closes_physical_authority_but_not_lifecycle(self):
        guard = self.armed(); receipt = guard.record_input_released(self.release())
        self.assertEqual(receipt["state"], RELEASED_PENDING)
        self.assertFalse(receipt["current_input_authority"])
        self.assertFalse(receipt["physical_input_may_be_down"])
        self.assertTrue(receipt["physical_release_verified"])
        self.assertTrue(receipt["program_terminal_pending"])
        terminal = {"event": "terminal", "id": "p1", "status": "cancelled",
            "terminal_ns": 310, "release": {"verified": True, "keys_down": [],
            "buttons_down": [], "verified_ns": 309}}
        closed = guard.record_cancelled_terminal(terminal)
        self.assertEqual(closed["state"], "REVOKED_ACTION_NOT_CURRENT")
        self.assertFalse(closed["program_terminal_pending"])

    def test_wrong_token_unverified_or_early_timestamp_rejected(self):
        for mutate in (
            lambda row: row.update(intent_token="wrong"),
            lambda row: row["owner_release"].update(verified=False),
            lambda row: row["owner_release"].update(verified_ns=301),
            lambda row: row.update(program_terminal_pending=False)):
            guard = self.armed(); row = self.release(); mutate(row)
            with self.assertRaises(ValueError): guard.record_input_released(row)

    def test_early_release_does_not_replace_terminal(self):
        guard = self.armed(); guard.record_input_released(self.release())
        with self.assertRaises(ValueError):
            guard.record_cancelled_terminal({"event": "terminal", "id": "p1",
                "status": "cancelled", "terminal_ns": 310,
                "release": {"verified": True, "keys_down": [],
                            "buttons_down": [], "verified_ns": 301}})


if __name__ == "__main__": unittest.main()
