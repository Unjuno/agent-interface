import copy
import unittest

from research.analysis.extreme_tail_eligibility_6576_construction_v1.gate import decide


REFERENCE = {
    "endpoint_identity": "admission_to_neutral_v1",
    "mode_manifest": ["normal"],
    "observed_modes": ["normal"],
    "tail_events_by_mode": {"normal": 100},
    "min_tail_events_per_mode": 40,
    "temporal_stability": True,
    "dependence_checked": True,
    "censor_count": 0,
    "missing_endpoint_count": 0,
}


class GateConstructionTests(unittest.TestCase):
    def test_stationary_complete_reference_is_eligible(self):
        self.assertEqual(decide(REFERENCE), "ELIGIBLE_REFERENCE")

    def test_declared_but_unseen_mode_is_not_estimable(self):
        row = copy.deepcopy(REFERENCE)
        row["mode_manifest"] = ["normal", "cleanup"]
        self.assertEqual(decide(row), "NOT_ESTIMABLE_MODE_COVERAGE")

    def test_explicit_drift_is_not_estimable(self):
        row = copy.deepcopy(REFERENCE)
        row["temporal_stability"] = False
        self.assertEqual(decide(row), "NOT_ESTIMABLE_NONSTATIONARY")

    def test_declared_mode_with_too_few_independent_tail_events_is_not_estimable(self):
        row = copy.deepcopy(REFERENCE)
        row["mode_manifest"] = ["normal", "cleanup"]
        row["observed_modes"] = ["normal", "cleanup"]
        row["tail_events_by_mode"] = {"normal": 100, "cleanup": 39}
        self.assertEqual(decide(row), "NOT_ESTIMABLE_INSUFFICIENT_TAIL_EVENTS")

    def test_unchecked_dependence_is_not_estimable(self):
        row = copy.deepcopy(REFERENCE)
        row["dependence_checked"] = False
        self.assertEqual(decide(row), "NOT_ESTIMABLE_DEPENDENCE")

    def test_censoring_is_never_silently_counted_as_on_time(self):
        row = copy.deepcopy(REFERENCE)
        row["censor_count"] = 1
        self.assertEqual(decide(row), "NOT_ESTIMABLE_CENSORED_ENDPOINT")

    def test_missing_endpoint_is_not_estimable(self):
        row = copy.deepcopy(REFERENCE)
        row["missing_endpoint_count"] = 1
        self.assertEqual(decide(row), "NOT_ESTIMABLE_MISSING_ENDPOINT")

    def test_missing_evidence_fails_closed(self):
        row = copy.deepcopy(REFERENCE)
        del row["censor_count"]
        self.assertEqual(decide(row), "NOT_ESTIMABLE_INCOMPLETE_EVIDENCE")

    def test_malformed_mode_metadata_fails_closed(self):
        row = copy.deepcopy(REFERENCE)
        row["mode_manifest"] = "normal"
        self.assertEqual(decide(row), "NOT_ESTIMABLE_MODE_METADATA")


if __name__ == "__main__":
    unittest.main()
