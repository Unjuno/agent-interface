"""Mutation tests for C02 admission/keymap temporal binding."""
import copy
import tempfile
import unittest
from pathlib import Path

import audit_temporal_v2 as audit_v2
from test_audit import make_fixture


class TemporalBindingTests(unittest.TestCase):
    def _fixture(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        raw, cases, freeze, started, environment = make_fixture(Path(temp.name))
        # Times are [pre finish, admitted, ack, post start, post finish].
        for index, occurrence in enumerate(raw["occurrences"]):
            offset = index * 100
            raw["events"][index * 2]["admitted_ns"] = 12 + offset
            raw["events"][index * 2]["input_ack_ns"] = 15 + offset
            raw["events"][index * 2]["valid_until_ns"] = 40 + offset
        return temp, raw, cases, freeze, started, environment

    def test_ordered_admission_and_ack_inside_down_witness_pass(self):
        _, raw, cases, _, _, _ = self._fixture()
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertTrue(result["all_occurrences_temporally_bound"], result)

    def test_admission_before_pre_down_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["admitted_ns"] = 9
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_ack_after_post_down_sample_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["input_ack_ns"] = 22
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_admission_after_down_witness_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["admitted_ns"] = 22
        raw["events"][0]["input_ack_ns"] = 23
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_missing_or_duplicate_admission_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        del raw["events"][0]["input_ack_ns"]
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_temporal_audit_rejects_missing_times_accepted_by_parent_audit(self):
        temp, raw, cases, freeze, started, environment = self._fixture()
        previous_root = audit_v2.parent_audit.ROOT
        audit_v2.parent_audit.ROOT = Path(temp.name)
        self.addCleanup(setattr, audit_v2.parent_audit, "ROOT", previous_root)
        for event in raw["events"]:
            event.pop("admitted_ns", None)
            event.pop("input_ack_ns", None)
        parent_checks = audit_v2.parent_audit.evaluate(
            raw, cases, freeze, started, environment)
        self.assertTrue(all(parent_checks.values()), parent_checks)
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_duplicate_admission_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"].append(copy.deepcopy(raw["events"][0]))
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_ack_at_or_after_lease_deadline_fails(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["valid_until_ns"] = 15
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_cross_occurrence_timestamps_fail(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"][0]["admitted_ns"] = 112
        raw["events"][0]["input_ack_ns"] = 115
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])

    def test_malformed_occurrence_or_event_fails_closed(self):
        _, raw, cases, _, _, _ = self._fixture()
        raw["events"].append(None)
        raw["occurrences"][0] = None
        result = audit_v2.evaluate_temporal_binding(raw, cases)
        self.assertFalse(result["all_occurrences_temporally_bound"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
