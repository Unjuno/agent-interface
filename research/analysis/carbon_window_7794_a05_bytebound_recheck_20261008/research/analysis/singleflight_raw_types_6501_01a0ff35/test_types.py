"""Regression: equal-valued JSON type changes must not pass raw replay."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from auditor_v2 import audit

ROOT = Path(__file__).resolve().parent
FIXTURE_BYTES = (ROOT / "fixtures.json").read_bytes()
FIXTURES = json.loads(FIXTURE_BYTES)
RAW = json.loads((ROOT / "retained-raw.json").read_bytes())
DIGEST = hashlib.sha256(FIXTURE_BYTES).hexdigest()


def integer_leaves(value, path=()):
    if type(value) is int:
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from integer_leaves(child, path + (key,))


def changed(path, value):
    raw = copy.deepcopy(RAW)
    parent = raw
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    return raw


class JsonTypeBoundary(unittest.TestCase):
    def test_unchanged_retained_raw_passes(self):
        self.assertEqual(audit(RAW, FIXTURES, DIGEST)["status"], "PASS_METHOD_SCOPED")

    def test_every_integer_as_float_is_rejected(self):
        # Removing type-sensitive comparison recreates this failure.
        for path, value in integer_leaves(RAW):
            with self.subTest(path=path):
                self.assertEqual(audit(changed(path, float(value)), FIXTURES, DIGEST)["status"], "FAIL_RAW_AUDIT")

    def test_zero_and_one_as_boolean_are_rejected(self):
        for path, value in integer_leaves(RAW):
            if value in (0, 1):
                with self.subTest(path=path):
                    self.assertEqual(audit(changed(path, bool(value)), FIXTURES, DIGEST)["status"], "FAIL_RAW_AUDIT")

    def test_changed_numeric_value_is_rejected(self):
        path = ("cases", "equivalent_overlap", "scope_typed", "verifier_invocations")
        self.assertEqual(audit(changed(path, 2), FIXTURES, DIGEST)["status"], "FAIL_RAW_AUDIT")

    def test_missing_case_is_rejected(self):
        raw = copy.deepcopy(RAW)
        del raw["cases"]["restart_aba"]
        self.assertEqual(audit(raw, FIXTURES, DIGEST)["status"], "FAIL_RAW_AUDIT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
