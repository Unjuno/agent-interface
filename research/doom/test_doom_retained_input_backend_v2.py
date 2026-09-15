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
wrapper = types.ModuleType("input_transition_owner_v2")
wrapper.InputOwner = object
sys.modules["input_transition_owner_v2"] = wrapper
spec = importlib.util.spec_from_file_location(
    "candidate", HERE / "doom_retained_input_backend_v2.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class Owner:
    def __init__(self, log, owned_after=None, ordinary=True):
        self.log = log
        self.owned_after = [] if owned_after is None else list(owned_after)
        self.ordinary = ordinary
    def call(self, op, lease=None, key=None):
        self.log.append((op, key))
        if op == "down":
            return {"event": "input_admission", "key": key}
        if op == "up":
            return {"event": "input_release_transition", "operation": "up", "key": key,
                    "ordinary_release_candidate": self.ordinary,
                    "owner_transition_verified": None}
        if op == "input_state":
            return {"owned_keycodes": list(self.owned_after),
                    "sample_started_ns": 100, "sample_finished_ns": 110}
        raise AssertionError(op)


def make_backend(held, owner):
    obj = candidate.Backend.__new__(candidate.Backend)
    obj.owner = owner
    obj.lease = object()
    obj.held = set(held)
    obj._release_batch = threading.local()
    obj._release_batch.rows = []
    return obj


class Tests(unittest.TestCase):
    def test_two_key_release_has_no_sample_or_emit_between_key_ups(self):
        log = []; owner = Owner(log); obj = make_backend({"a", "space"}, owner)
        obj.emit = lambda row: log.append(("emit", row["key"]))
        obj.raw("a", False)
        self.assertEqual(log, [("up", "a")])
        obj.raw("space", False)
        self.assertEqual(log, [
            ("up", "a"), ("up", "space"), ("input_state", None),
            ("emit", "a"), ("emit", "space")])

    def test_batch_verification_is_shared_after_final_release(self):
        log = []; owner = Owner(log); obj = make_backend({"a", "space"}, owner); rows = []
        obj.emit = rows.append
        obj.raw("a", False); obj.raw("space", False)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["owner_transition_verified"] for row in rows))
        self.assertEqual([row["release_batch_position"] for row in rows], [0, 1])
        self.assertTrue(all(row["release_batch_size"] == 2 for row in rows))

    def test_nonordinary_cleanup_fails_closed_as_direct_measurement(self):
        log = []; owner = Owner(log, ordinary=False); obj = make_backend({"a"}, owner); rows = []
        obj.emit = rows.append
        obj.raw("a", False)
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_nonempty_owner_state_after_batch_fails_closed(self):
        log = []; owner = Owner(log, owned_after=[38]); obj = make_backend({"a"}, owner); rows = []
        obj.emit = rows.append
        obj.raw("a", False)
        self.assertFalse(rows[0]["owner_transition_verified"])
        self.assertEqual(rows[0]["owned_keycodes_after_batch"], [38])

    def test_unowned_backend_release_fails_closed(self):
        log = []; owner = Owner(log); obj = make_backend(set(), owner); rows = []
        obj.emit = rows.append
        obj.raw("a", False)
        self.assertFalse(rows[0]["backend_owned_before_release"])
        self.assertFalse(rows[0]["owner_transition_verified"])

    def test_key_down_behavior_still_emits_admission(self):
        log = []; owner = Owner(log); obj = make_backend(set(), owner); rows = []
        obj.emit = rows.append
        obj.raw("a", True)
        self.assertEqual(obj.held, {"a"})
        self.assertEqual(rows, [{"event": "input_admission", "key": "a"}])
        self.assertEqual(log, [("down", "a")])


if __name__ == "__main__": unittest.main()
