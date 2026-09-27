import importlib.util
import sys
import threading
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

parent = types.ModuleType("doom_typed_coast_backend_v1")
parent.Backend = object
parent.suite = object()
sys.modules["doom_typed_coast_backend_v1"] = parent
wrapper = types.ModuleType("input_transition_owner_v3")
wrapper.InputOwner = object
sys.modules["input_transition_owner_v3"] = wrapper

spec = importlib.util.spec_from_file_location(
    "candidate", HERE / "doom_retained_input_backend_v4.py"
)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class Lease:
    def __init__(
        self,
        deadline=1_000,
        token="intent-1",
        expected_focus=99,
        focus_invalid=False,
        interruption=None,
    ):
        self.deadline = deadline
        self.intent_token = token
        self.expected_focus = expected_focus
        self.focus_invalid = focus_invalid
        self._interruption = interruption

    def interruption_snapshot(self):
        return self._interruption


class Owner:
    def __init__(
        self,
        log,
        *,
        owner_id="owner-1",
        owned_after=None,
        sample_started_ns=100,
        sample_finished_ns=110,
        cancel_requested=False,
        active_lease_time_valid=True,
        active_lease_deadline_ns=1_000,
        focus=99,
        receipt_token="intent-1",
        ordinary=True,
    ):
        self.log = log
        self.owner_id = owner_id
        self.owned_after = [] if owned_after is None else list(owned_after)
        self.sample_started_ns = sample_started_ns
        self.sample_finished_ns = sample_finished_ns
        self.cancel_requested = cancel_requested
        self.active_lease_time_valid = active_lease_time_valid
        self.active_lease_deadline_ns = active_lease_deadline_ns
        self.focus = focus
        self.receipt_token = receipt_token
        self.ordinary = ordinary
        self.release_index = 0

    def call(self, op, lease=None, key=None):
        self.log.append((op, key))
        if op == "down":
            return {"event": "input_admission", "key": key}
        if op == "up":
            self.release_index += 1
            returned = self.release_index * 10
            return {
                "event": "input_release_transition",
                "transition_schema": "input-release-transition-v3",
                "operation": "up",
                "key": key,
                "owner_id": self.owner_id,
                "intent_token": self.receipt_token,
                "release_call_started_ns": returned - 5,
                "release_call_returned_ns": returned,
                "ordinary_release_candidate": self.ordinary,
                "owner_transition_verified": None,
            }
        if op == "input_state":
            return {
                "owner_id": self.owner_id,
                "owned_keycodes": list(self.owned_after),
                "sample_started_ns": self.sample_started_ns,
                "sample_finished_ns": self.sample_finished_ns,
                "cancel_requested": self.cancel_requested,
                "active_lease_time_valid": self.active_lease_time_valid,
                "active_lease_deadline_ns": self.active_lease_deadline_ns,
                "focus": self.focus,
            }
        raise AssertionError(op)


def make_backend(held, owner, lease=None):
    obj = candidate.Backend.__new__(candidate.Backend)
    obj.owner = owner
    obj.lease = Lease() if lease is None else lease
    obj.held = set(held)
    obj._release_batch = threading.local()
    obj._release_batch.context = {"rows": [], "identifier": "p1", "step": 0}
    return obj


class Tests(unittest.TestCase):
    def run_release(self, owner, lease=None, held=("a",)):
        obj = make_backend(set(held), owner, lease)
        rows = []
        obj.emit = rows.append
        for key in held:
            obj.raw(key, False)
        return obj, rows

    def test_two_key_order_remains_up_up_sample_then_emit(self):
        log = []
        owner = Owner(log)
        obj = make_backend({"a", "space"}, owner)
        obj.emit = lambda row: log.append(("emit", row["key"]))
        obj.raw("a", False)
        self.assertEqual(log, [("up", "a")])
        obj.raw("space", False)
        self.assertEqual(log, [
            ("up", "a"),
            ("up", "space"),
            ("input_state", None),
            ("emit", "a"),
            ("emit", "space"),
        ])

    def test_clean_post_batch_authority_verifies(self):
        _, rows = self.run_release(Owner([]))
        self.assertTrue(rows[0]["post_batch_authority_verified"])
        self.assertTrue(rows[0]["owner_transition_verified"])
        self.assertEqual(rows[0]["release_batch_schema"], "input-release-batch-v4")

    def test_recorded_interruption_after_release_request_fails_closed(self):
        lease = Lease(interruption={
            "intent_token": "intent-1",
            "record": {"event": "owner_release", "reason": "cancelled"},
        })
        _, rows = self.run_release(Owner([]), lease)
        self.assertFalse(rows[0]["interruption_clear"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_cancel_visible_only_in_post_batch_sample_fails_closed(self):
        _, rows = self.run_release(Owner([], cancel_requested=True))
        self.assertFalse(rows[0]["post_cancel_clear"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_expiry_visible_only_in_post_batch_sample_fails_closed(self):
        _, rows = self.run_release(Owner([], active_lease_time_valid=False))
        self.assertFalse(rows[0]["post_lease_time_valid"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_active_deadline_mismatch_fails_closed(self):
        _, rows = self.run_release(Owner([], active_lease_deadline_ns=999))
        self.assertFalse(rows[0]["active_deadline_matches"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_local_focus_invalid_fails_closed(self):
        lease = Lease(focus_invalid=True)
        _, rows = self.run_release(Owner([]), lease)
        self.assertFalse(rows[0]["local_focus_invalid_clear"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_sampled_focus_mismatch_fails_closed(self):
        _, rows = self.run_release(Owner([], focus=100))
        self.assertFalse(rows[0]["sampled_focus_matches"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_missing_interruption_api_fails_closed(self):
        class WeakLease:
            deadline = 1_000
            intent_token = "intent-1"
            expected_focus = 99
            focus_invalid = False
        _, rows = self.run_release(Owner([]), WeakLease())
        self.assertFalse(rows[0]["interruption_clear"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_existing_v3_sample_order_failure_still_fails(self):
        _, rows = self.run_release(Owner([], sample_started_ns=9, sample_finished_ns=11))
        self.assertFalse(rows[0]["owner_sample_ordered_after_batch"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_existing_v3_owner_identity_failure_still_fails(self):
        owner = Owner([])
        original = owner.call
        def call(op, lease=None, key=None):
            row = original(op, lease, key)
            if op == "input_state":
                row["owner_id"] = "other-owner"
            return row
        owner.call = call
        _, rows = self.run_release(owner)
        self.assertFalse(rows[0]["owner_identity_matches_after_batch"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_existing_v3_token_failure_still_fails(self):
        _, rows = self.run_release(Owner([], receipt_token="other-intent"))
        self.assertFalse(rows[0]["intent_token_matches_after_batch"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_existing_v3_nonempty_owner_state_still_fails(self):
        _, rows = self.run_release(Owner([], owned_after=[38]))
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_request_time_stale_flag_still_fails(self):
        _, rows = self.run_release(Owner([], ordinary=False))
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_backend_unowned_release_still_fails(self):
        owner = Owner([])
        obj = make_backend(set(), owner)
        rows = []
        obj.emit = rows.append
        obj.raw("a", False)
        self.assertFalse(rows[0]["backend_owned_before_release"])
        self.assertFalse(rows[0]["owner_transition_verified"])


if __name__ == "__main__":
    unittest.main()
