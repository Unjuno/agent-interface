import copy
import hashlib
import json
import os
import unittest
from pathlib import Path

from audit_oracle import reconstruct
from binding_candidate import evaluate


FIXTURE = Path(os.environ["W2_TRACE_FIXTURE"])
EXPECTED_SHA256 = "6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f"
NEEDS_BINDING = {
    "release-before-terminal": "A4",
    "overlapping-key-holds": "A5",
    "missing-and-out-of-order-edge": "A6",
    "held-input-no-effect": "A8",
}


class LeaseActuationBindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = FIXTURE.read_bytes()
        if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
            raise AssertionError("frozen W2 fixture hash mismatch")
        cls.document = json.loads(raw)

    def _case(self, case_id):
        return copy.deepcopy(next(c for c in self.document["cases"] if c["case_id"] == case_id))

    @staticmethod
    def _bind(case, actuation_id):
        for event in case["events"]:
            if event["event_type"] == "LEASE_OPEN":
                event["lineage"]["actuation_id"] = actuation_id

    def test_original_baseline_runner_fixture_is_unchanged_and_eight_cases_exist(self):
        self.assertEqual(len(self.document["cases"]), 8)
        self.assertEqual(set(NEEDS_BINDING), {
            "release-before-terminal", "overlapping-key-holds",
            "missing-and-out-of-order-edge", "held-input-no-effect",
        })

    def test_four_legacy_authorized_input_cases_hold_when_open_binding_is_absent(self):
        for case_id in NEEDS_BINDING:
            with self.subTest(case_id=case_id):
                events = self._case(case_id)["events"]
                self.assertTrue(any(e["event_type"] == "LEASE_OPEN" for e in events))
                self.assertTrue(any(e["event_type"] == "INPUT_EDGE_BRACKET" for e in events))
                self.assertEqual(evaluate(events), reconstruct(events))
                self.assertTrue(all(x["status"] == "HOLD_MISSING_LEASE_ACTUATION" for x in evaluate(events)))

    def test_versioned_matched_positive_foreign_and_missing_controls(self):
        counts = {"matched": 0, "mismatch": 0, "missing": 0}
        for case_id, expected_actuation in NEEDS_BINDING.items():
            with self.subTest(case_id=case_id):
                positive = self._case(case_id)
                self._bind(positive, expected_actuation)
                p = evaluate(positive["events"])
                self.assertEqual(p, reconstruct(positive["events"]))
                self.assertTrue(all(x["status"] == "AUTHORIZED_MATCH" for x in p))
                counts["matched"] += 1

                foreign = copy.deepcopy(positive)
                self._bind(foreign, "FOREIGN-ACTUATION")
                f = evaluate(foreign["events"])
                self.assertEqual(f, reconstruct(foreign["events"]))
                self.assertTrue(all(x["status"] == "REJECT_ACTUATION_MISMATCH" for x in f))
                counts["mismatch"] += 1

                missing = copy.deepcopy(positive)
                self._bind(missing, None)
                m = evaluate(missing["events"])
                self.assertEqual(m, reconstruct(missing["events"]))
                self.assertTrue(all(x["status"] == "HOLD_MISSING_LEASE_ACTUATION" for x in m))
                counts["missing"] += 1
        self.assertEqual(counts, {"matched": 4, "mismatch": 4, "missing": 4})

    def test_reused_lease_id_is_ambiguous(self):
        case = self._case("release-before-terminal")
        self._bind(case, "A4")
        second = copy.deepcopy(next(e for e in case["events"] if e["event_type"] == "LEASE_OPEN"))
        second["event_id"] = "synthetic-second-open"
        second["lineage"]["actuation_id"] = "OTHER"
        case["events"].append(second)
        result = evaluate(case["events"])
        self.assertEqual(result, reconstruct(case["events"]))
        self.assertTrue(all(x["status"] == "HOLD_AMBIGUOUS_LEASE_BINDING" for x in result))

    def test_edge_without_lease_open_holds(self):
        case = self._case("unauthorized-input-after-expiry")
        result = evaluate(case["events"])
        self.assertEqual(result, reconstruct(case["events"]))
        self.assertTrue(all(x["status"] == "HOLD_LEASE_OPEN_MISSING" for x in result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
