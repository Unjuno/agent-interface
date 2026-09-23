import importlib.util
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
parent = types.ModuleType("doom_typed_coast_backend_v1")
parent.Backend = object
parent.suite = object()
sys.modules["doom_typed_coast_backend_v1"] = parent
wrapper = types.ModuleType("input_transition_owner_v1")
wrapper.InputOwner = object
sys.modules["input_transition_owner_v1"] = wrapper
spec = importlib.util.spec_from_file_location("candidate", HERE / "doom_retained_input_backend_v1.py")
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class Owner:
    def __init__(self): self.after = 1
    def call(self, op, lease, key):
        if op == "up":
            return {"event": "input_release_transition", "operation": "up", "key": key,
                    "owned_count_after": self.after, "owner_transition_verified": None}
        return {"event": "input_admission", "key": key}


class Tests(unittest.TestCase):
    def test_backend_verifies_expected_owner_count_without_pre_release_probe(self):
        obj = candidate.Backend.__new__(candidate.Backend)
        obj.owner = Owner(); obj.lease = object(); obj.held = {"Up", "Shift_L"}; rows = []
        obj.emit = rows.append
        obj.raw("Up", False)
        self.assertEqual(obj.held, {"Shift_L"})
        self.assertTrue(rows[-1]["owner_transition_verified"])
        self.assertEqual(rows[-1]["expected_owned_count_after"], 1)

    def test_stale_backend_owner_mismatch_fails_closed(self):
        obj = candidate.Backend.__new__(candidate.Backend)
        obj.owner = Owner(); obj.owner.after = 0; obj.lease = object(); obj.held = {"Up", "Shift_L"}; rows = []
        obj.emit = rows.append
        obj.raw("Up", False)
        self.assertFalse(rows[-1]["owner_transition_verified"])

    def test_unowned_backend_release_fails_closed_even_if_count_matches(self):
        obj = candidate.Backend.__new__(candidate.Backend)
        obj.owner = Owner(); obj.owner.after = 1; obj.lease = object(); obj.held = {"Shift_L"}; rows = []
        obj.emit = rows.append
        obj.raw("Up", False)
        self.assertFalse(rows[-1]["backend_owned_before_release"])
        self.assertFalse(rows[-1]["owner_transition_verified"])


if __name__ == "__main__": unittest.main()
