import importlib.util
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
stub = types.ModuleType("input_owner_v10")
stub.InputOwner = object
sys.modules["input_owner_v10"] = stub
spec = importlib.util.spec_from_file_location(
    "candidate", HERE / "input_transition_owner_v2.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class Cancel:
    def __init__(self, value=False): self.value = value
    def is_set(self): return self.value


class Lease:
    def __init__(self, deadline=1_000, cancelled=False, focus_invalid=False):
        self.deadline = deadline
        self.cancel = Cancel(cancelled)
        self.focus_invalid = focus_invalid
        self.intent_token = "intent-1"


class Inner:
    def __init__(self, _display):
        self.owner_id = "owner-1"
        self.records = []
        self.operations = []
        self.next = None
    def call(self, op, lease=None, key=None):
        self.operations.append((op, key))
        if op == "release":
            return {"event": "owner_release", "verified": True}
        return self.next
    def close(self):
        self.operations.append(("close", None))


def set_clock(*values):
    iterator = iter(values)
    candidate.time.perf_counter_ns = lambda: next(iterator)


class Tests(unittest.TestCase):
    def make(self):
        owner = candidate.InputOwner(":test", _owner_cls=Inner)
        return owner, owner._inner

    def test_up_does_not_sample_input_state_between_releases(self):
        owner, inner = self.make(); lease = Lease()
        set_clock(100, 120)
        row = owner.call("up", lease, "a")
        self.assertEqual(inner.operations, [("up", "a")])
        self.assertEqual(row["transition_schema"], "input-release-transition-v2")
        self.assertEqual(row["release_call_bracket_ns"], 20)
        self.assertTrue(row["ordinary_release_candidate"])
        self.assertIsNone(row["owner_transition_verified"])

    def test_cancelled_release_is_not_ordinary_candidate(self):
        owner, inner = self.make(); lease = Lease(cancelled=True)
        set_clock(100, 120)
        row = owner.call("up", lease, "a")
        self.assertFalse(row["ordinary_release_candidate"])
        self.assertTrue(row["cancel_requested_at_request"])
        self.assertEqual(inner.operations, [("up", "a")])

    def test_expired_or_focus_invalid_release_is_not_ordinary_candidate(self):
        owner, _ = self.make(); lease = Lease(deadline=99)
        set_clock(100, 120)
        self.assertFalse(owner.call("up", lease, "a")["ordinary_release_candidate"])
        owner, _ = self.make(); lease = Lease(focus_invalid=True)
        set_clock(100, 120)
        row = owner.call("up", lease, "a")
        self.assertFalse(row["ordinary_release_candidate"])
        self.assertTrue(row["focus_invalid_at_request"])

    def test_nonrelease_operation_is_delegated_without_extra_sampling(self):
        owner, inner = self.make(); inner.next = {"owner_id": "owner-1"}
        result = owner.call("input_state")
        self.assertEqual(result, {"owner_id": "owner-1"})
        self.assertEqual(inner.operations, [("input_state", None)])

    def test_aggregate_owner_release_keeps_intent_provenance(self):
        owner, inner = self.make(); lease = Lease()
        set_clock(100, 130)
        row = owner.call("release", lease)
        self.assertEqual(inner.operations, [("release", None)])
        self.assertEqual(row["intent_token"], "intent-1")
        self.assertEqual(row["release_call_started_ns"], 100)
        self.assertEqual(row["release_call_returned_ns"], 130)


if __name__ == "__main__": unittest.main()
