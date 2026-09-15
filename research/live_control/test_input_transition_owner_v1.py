import importlib.util
import sys
import time
import types
import unittest
from pathlib import Path

stub = types.ModuleType("input_owner_v10")
stub.InputOwner = object
sys.modules.setdefault("input_owner_v10", stub)
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("candidate", HERE / "input_transition_owner_v1.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class Lease:
    deadline = 9_999_999_999
    intent_token = "intent-1"


class FakeOwner:
    def __init__(self, _display):
        self.owner_id = "owner-1"
        self.records = []
        self.keys = [38]
        self.buttons = [1]
        self.revision = 1
        self.state_calls = 0

    def close(self):
        return None

    def call(self, operation, lease=None, key=None):
        now = time.perf_counter_ns()
        if operation == "input_state":
            self.state_calls += 1
            return {"owner_id": self.owner_id, "revision": self.revision,
                    "sample_started_ns": now, "sample_finished_ns": now + 1,
                    "owned_keycodes": list(self.keys), "owned_buttons": list(self.buttons),
                    "physical_pointer_mask": 0, "pointer": [0, 0], "focus": 1,
                    "active_lease_deadline_ns": getattr(lease, "deadline", None),
                    "active_lease_time_valid": True, "cancel_requested": False}
        if operation == "up":
            if self.keys: self.keys.pop()
            self.revision += 1
            return None
        if operation == "button_up":
            if self.buttons: self.buttons.pop()
            self.revision += 1
            return None
        if operation == "down":
            return {"event": "input_admission", "key": key,
                    "admitted_ns": now, "input_ack_ns": now + 1,
                    "valid_until_ns": getattr(lease, "deadline", None)}
        if operation == "release":
            rec = {"event": "owner_release", "reason": "release", "verified": True,
                   "keys_down": [], "buttons_down": [], "verified_ns": now}
            self.records.append(rec)
            return rec
        raise AssertionError(operation)


class Tests(unittest.TestCase):
    def test_key_release_has_bracket_token_and_only_post_sample(self):
        owner = candidate.InputOwner(":fake", _owner_cls=FakeOwner)
        rec = owner.call("up", Lease(), "a")
        self.assertEqual(rec["event"], "input_release_transition")
        self.assertIsNone(rec["owner_transition_verified"])
        self.assertEqual(rec["owned_count_after"], 0)
        self.assertEqual(rec["intent_token"], "intent-1")
        self.assertEqual(owner._inner.state_calls, 1)
        self.assertLessEqual(rec["release_call_started_ns"], rec["release_call_returned_ns"])

    def test_button_release_has_bracket(self):
        owner = candidate.InputOwner(":fake", _owner_cls=FakeOwner)
        rec = owner.call("button_up", Lease(), 1)
        self.assertEqual(rec["owned_count_after"], 0)
        self.assertEqual(rec["button"], 1)

    def test_admission_is_decorated_with_intent_token(self):
        owner = candidate.InputOwner(":fake", _owner_cls=FakeOwner)
        rec = owner.call("down", Lease(), "a")
        self.assertEqual(rec["intent_token"], "intent-1")

    def test_release_all_gets_call_bracket(self):
        owner = candidate.InputOwner(":fake", _owner_cls=FakeOwner)
        rec = owner.call("release", Lease())
        self.assertLessEqual(rec["release_call_started_ns"], rec["release_call_returned_ns"])
        self.assertEqual(rec["intent_token"], "intent-1")


if __name__ == "__main__":
    unittest.main()
