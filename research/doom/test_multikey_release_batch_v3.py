"""Synthetic two-key release batch controls for the opt-in v14 backend.

These tests use fake owner state and validate software receipt attribution only.
They do not exercise X11, physical key release, or application effects.
"""
import sys
import threading
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

class FakeOwner:
    mode = "normal"

    def __init__(self, display_name):
        self.owner_id = "owner-multikey"
        self.records = []
        self.sequence = 0
        self.display_name = display_name

    def close(self):
        pass

    def call(self, operation, lease=None, key=None):
        if operation == "down":
            return None
        if operation == "up":
            self.sequence += 1
            base = self.sequence * 100
            receipt = {
                "event": "owner_explicit_keyup",
                "operation": "up",
                "key": key,
                "keycode": {"a": 38, "space": 65}[key],
                "owner_id": self.owner_id,
                "intent_token": lease.intent_token,
                "valid_until_ns": lease.deadline,
                "owner_keyrelease_started_ns": base,
                "owner_sync_returned_ns": base + 2,
                "server_sync_completed": True,
                "physical_verification_authoritative": False,
            }
            if not (self.mode == "missing_history" and key == "space"):
                self.records.append(receipt)
                if self.mode == "duplicate_history" and key == "space":
                    self.records.append(dict(receipt))
            return {
                "event": "input_release_transition",
                "operation": "up",
                "key": key,
                "owner_id": self.owner_id,
                "intent_token": lease.intent_token,
                "valid_until_ns": lease.deadline,
                "release_call_started_ns": base - 2,
                "release_call_returned_ns": base + 4,
                "ordinary_release_candidate": True,
                "owner_thread_keyup_verified": True,
                "owner_thread_keyup_receipt": dict(receipt),
            }
        if operation == "input_state":
            sample = self.sequence * 100 + 10
            return {
                "owner_id": self.owner_id,
                "sample_started_ns": sample,
                "sample_finished_ns": sample + 1,
                "owned_keycodes": [],
            }
        raise AssertionError(operation)

base_module = types.ModuleType("doom_typed_release_backend_v2")

class FakePrevious:
    def __init__(self, session, out, emit, signal_readers):
        self.owner = FakeOwner(session.name)
        self.held = set()
        self.emit = emit
        self._input_event_context = None
        self.lease = types.SimpleNamespace(
            intent_token="lease-multikey", deadline=999)

    def execute(self, step, cancel, identifier, index):
        self._input_event_context = (identifier, index)
        try:
            for key in step["keys"]:
                self.raw(key, True)
            for key in step["keys"]:
                self.raw(key, False)
        finally:
            self._input_event_context = None

    def release_all(self):
        return {"verified": True}

base_module.Backend = FakePrevious
base_module.suite = object()
sys.modules["doom_typed_release_backend_v2"] = base_module
wrapper_module = types.ModuleType("input_transition_owner_v4")
wrapper_module.InputOwner = FakeOwner
sys.modules["input_transition_owner_v4"] = wrapper_module
import doom_typed_release_backend_v3 as candidate

class MultiKeyReleaseBatchTests(unittest.TestCase):
    def run_batch(self, mode):
        FakeOwner.mode = mode
        events = []
        backend = candidate.Backend(
            types.SimpleNamespace(name="display"), None, events.append, {})
        backend.execute(
            {"keys": ["a", "space"]}, None, "program-multikey", 7)
        return [row for row in events
                if row.get("event") == "input_release_transition"]

    def test_two_key_receipts_keep_identity_order_and_distinct_bounds(self):
        rows = self.run_batch("normal")
        self.assertEqual([row["key"] for row in rows], ["a", "space"])
        self.assertEqual([row["release_batch_position"] for row in rows], [0, 1])
        self.assertEqual([row["release_batch_size"] for row in rows], [2, 2])
        self.assertTrue(all(row["owner_transition_verified"] for row in rows))
        self.assertEqual(
            [row["owner_thread_keyup_receipt"]["key"] for row in rows],
            ["a", "space"])
        self.assertEqual(
            [(row["release_call_started_ns"], row["release_call_returned_ns"])
             for row in rows],
            [(98, 104), (198, 204)])

    def test_missing_second_owner_history_row_fails_closed(self):
        rows = self.run_batch("missing_history")
        self.assertEqual(len(rows), 2)
        self.assertFalse(any(row["owner_transition_verified"] for row in rows))

    def test_duplicate_second_owner_history_row_fails_closed(self):
        rows = self.run_batch("duplicate_history")
        self.assertEqual(len(rows), 2)
        self.assertFalse(any(row["owner_transition_verified"] for row in rows))

if __name__ == "__main__":
    unittest.main(verbosity=2)
