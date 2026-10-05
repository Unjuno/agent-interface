import unittest
import hashlib
import json
import copy
from pathlib import Path

import audit
import candidate


def make_fixture():
    return json.loads((Path(__file__).parent / "fixture.json").read_text())


class IncorrectBeliefExposureConstructionTests(unittest.TestCase):
    def extract(self, rows):
        function = getattr(candidate, "extract_observations", None)
        self.assertTrue(callable(function), "candidate must expose observable age/effect extraction")
        return function(rows)

    def adjudicate(self, fixture, raw, frozen_digest=None):
        function = getattr(audit, "adjudicate", None)
        self.assertTrue(callable(function), "auditor must adjudicate fixture truth independently")
        return function(fixture, raw, frozen_digest)

    def test_candidate_never_receives_truth_and_extracts_freshness_separately(self):
        fixture = make_fixture()
        raw = self.extract(fixture["candidate_view"])
        self.assertEqual(raw["old_correct"]["observation_age_ticks"], 10)
        self.assertEqual(raw["fresh_misbound"]["observation_age_ticks"], 1)
        self.assertNotIn("truth_state", str(raw))

    def test_truth_audit_distinguishes_old_correct_from_stale_and_fresh_wrong(self):
        fixture = make_fixture()
        raw = self.extract(fixture["candidate_view"])
        result = self.adjudicate(fixture, raw)
        rows = result["cases"]
        self.assertEqual((rows["old_correct"]["belief_error_ticks"], rows["old_correct"]["unsafe_admissibility_ticks"]), (0, 0))
        self.assertEqual((rows["stale_transition"]["belief_error_ticks"], rows["stale_transition"]["unsafe_admissibility_ticks"]), (6, 6))
        self.assertEqual((rows["fresh_misbound"]["belief_error_ticks"], rows["fresh_misbound"]["unsafe_admissibility_ticks"]), (5, 5))
        self.assertEqual(rows["fresh_misbound"]["observation_age_ticks"], 1)

    def test_exposure_requires_live_authority_and_action_opportunity(self):
        fixture = make_fixture()
        result = self.adjudicate(fixture, self.extract(fixture["candidate_view"]))
        self.assertEqual(result["cases"]["no_authority"]["unsafe_admissibility_ticks"], 0)
        self.assertEqual(result["cases"]["revoked_no_opportunity"]["unsafe_admissibility_ticks"], 0)

    def test_realized_unsafe_effect_is_separate_from_duration(self):
        fixture = make_fixture()
        result = self.adjudicate(fixture, self.extract(fixture["candidate_view"]))
        row = result["cases"]["unsafe_emission"]
        self.assertEqual(row["unsafe_admissibility_ticks"], 8)
        self.assertEqual(row["realized_unsafe_effects"], 1)
        self.assertEqual(row["effect_ages_ticks"], [5])

    def test_missing_truth_or_ambiguous_clock_returns_unknown_not_zero(self):
        fixture = make_fixture()
        result = self.adjudicate(fixture, self.extract(fixture["candidate_view"]))
        for case_id in ("unknown_truth", "ambiguous_clock"):
            row = result["cases"][case_id]
            self.assertEqual(row["status"], "UNKNOWN")
            self.assertIsNone(row["unsafe_admissibility_ticks"])
        self.assertIsNone(result["cases"]["ambiguous_clock"]["observation_age_ticks"])

    def test_raw_or_truth_mutations_are_rejected(self):
        fixture = make_fixture()
        raw = self.extract(fixture["candidate_view"])
        self.assertTrue(self.adjudicate(fixture, raw)["passed"])
        damaged = {key: dict(value) for key, value in raw.items()}
        damaged["stale_transition"]["observation_age_ticks"] = 0
        self.assertFalse(self.adjudicate(fixture, damaged)["passed"])
        changed = copy.deepcopy(fixture)
        changed["truth_sidecar"][1]["truth_state"] = "normal"
        digest = hashlib.sha256(json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertFalse(self.adjudicate(changed, raw, digest)["passed"])


if __name__ == "__main__":
    unittest.main()
