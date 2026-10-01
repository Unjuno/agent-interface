"""Append-only scalar-lease/multiple-actuation construction extension."""
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


class LeaseActuationBindingExtensionTest(unittest.TestCase):
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

    def test_fixture_is_the_unchanged_eight_case_source(self):
        self.assertEqual(len(self.document["cases"]), 8)
        self.assertEqual(set(NEEDS_BINDING), {
            "release-before-terminal", "overlapping-key-holds",
            "missing-and-out-of-order-edge", "held-input-no-effect",
        })

    def test_legacy_cases_without_open_binding_hold(self):
        for case_id in NEEDS_BINDING:
            with self.subTest(case_id=case_id):
                events = self._case(case_id)["events"]
                decisions = evaluate(events)
                self.assertEqual(decisions, reconstruct(events))
                self.assertTrue(all(x["status"] == "HOLD_MISSING_LEASE_ACTUATION" for x in decisions))

    def test_four_versioned_matches_and_one_field_negative_controls(self):
        counts = {"matched": 0, "foreign": 0, "missing": 0}
        for case_id, action in NEEDS_BINDING.items():
            with self.subTest(case_id=case_id):
                good = self._case(case_id)
                self._bind(good, action)
                match = evaluate(good["events"])
                self.assertEqual(match, reconstruct(good["events"]))
                self.assertTrue(all(x["status"] == "AUTHORIZED_MATCH" for x in match))
                counts["matched"] += 1
                for value, key in (("FOREIGN-ACTUATION", "foreign"), (None, "missing")):
                    bad = copy.deepcopy(good)
                    self._bind(bad, value)
                    verdicts = evaluate(bad["events"])
                    self.assertEqual(verdicts, reconstruct(bad["events"]))
                    expected = "REJECT_ACTUATION_MISMATCH" if key == "foreign" else "HOLD_MISSING_LEASE_ACTUATION"
                    self.assertTrue(all(x["status"] == expected for x in verdicts))
                    counts[key] += 1
        self.assertEqual(counts, {"matched": 4, "foreign": 4, "missing": 4})

    def test_reused_lease_id_with_distinct_opens_is_ambiguous(self):
        case = self._case("release-before-terminal")
        self._bind(case, "A4")
        second = copy.deepcopy(next(e for e in case["events"] if e["event_type"] == "LEASE_OPEN"))
        second["event_id"] = "synthetic-second-open"
        second["lineage"]["actuation_id"] = "OTHER"
        case["events"].append(second)
        verdicts = evaluate(case["events"])
        self.assertEqual(verdicts, reconstruct(case["events"]))
        self.assertTrue(all(x["status"] == "HOLD_AMBIGUOUS_LEASE_BINDING" for x in verdicts))

    def test_scalar_open_binding_does_not_cover_a_second_actuation(self):
        rows = [
            {"event_id": "open-1", "event_type": "LEASE_OPEN",
             "lineage": {"lease_id": "L1", "actuation_id": "A4"}},
            {"event_id": "edge-a4", "event_type": "INPUT_EDGE_BRACKET",
             "lineage": {"lease_id": "L1", "actuation_id": "A4"}},
            {"event_id": "edge-a5", "event_type": "INPUT_EDGE_BRACKET",
             "lineage": {"lease_id": "L1", "actuation_id": "A5"}},
        ]
        verdicts = evaluate(rows)
        self.assertEqual(verdicts, reconstruct(rows))
        self.assertEqual([x["status"] for x in verdicts], [
            "AUTHORIZED_MATCH", "REJECT_ACTUATION_MISMATCH",
        ])

    def test_input_edges_without_lease_open_hold(self):
        events = self._case("unauthorized-input-after-expiry")["events"]
        verdicts = evaluate(events)
        self.assertEqual(verdicts, reconstruct(events))
        self.assertTrue(all(x["status"] == "HOLD_LEASE_OPEN_MISSING" for x in verdicts))


if __name__ == "__main__":
    unittest.main(verbosity=2)
