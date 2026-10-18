import unittest

import analyze
import audit


def fixture_rows():
    rows = []
    for updater in ("CASE_PATCH", "STRATUM_PATCH"):
        for feedback in ("CONTROLLED", "FULL"):
            for seed in range(100):
                feedback_gain = 2 if updater == "CASE_PATCH" else 1
                dev = 16 + (feedback == "FULL") * feedback_gain + (updater == "STRATUM_PATCH")
                fresh = 16 + (updater == "STRATUM_PATCH")
                rows.append({
                    "updater": updater,
                    "feedback": feedback,
                    "seed": seed,
                    "dev_correct": int(dev),
                    "dev_total": 32,
                    "fresh_correct": int(fresh),
                    "fresh_total": 32,
                    "optimism": (dev - fresh) / 32,
                    "query_count": 5,
                    "safety_veto_count": 1,
                    "candidate_locked_before_fresh": True,
                    "raw_released_after_lock": True,
                })
    return rows


class AnalysisTests(unittest.TestCase):
    def test_factorial_means_and_interaction(self):
        result = analyze.summarize(fixture_rows(), "a" * 64)
        self.assertEqual(result["rows"], 400)
        self.assertEqual(
            result["feedback_full_minus_controlled_within_updater"]["CASE_PATCH"]["dev_accuracy"]["mean_fraction"],
            "1/16",
        )
        self.assertEqual(
            result["feedback_full_minus_controlled_within_updater"]["STRATUM_PATCH"]["dev_accuracy"]["mean_fraction"],
            "1/32",
        )
        self.assertEqual(
            result["interaction_case_minus_stratum_of_feedback_effect"]["dev_accuracy"]["mean_fraction"],
            "1/32",
        )

    def test_duplicate_or_missing_seed_is_rejected(self):
        rows = fixture_rows()
        with self.assertRaises(ValueError):
            analyze.validate_rows(rows[:-1])
        with self.assertRaises(ValueError):
            audit._rebuild(rows + [dict(rows[0])], "a" * 64)

    def test_exact_type_gate_rejects_bool_veto_count(self):
        rows = fixture_rows()
        rows[0]["safety_veto_count"] = True
        with self.assertRaises(ValueError):
            audit._rebuild(rows, "a" * 64)

    def test_analysis_mutation_gate_rejects_changed_summary(self):
        rows = fixture_rows()
        expected = audit._rebuild(rows, "a" * 64)
        changed = dict(expected)
        changed["rows"] = 399
        self.assertFalse(audit._analysis_matches(changed, expected))


if __name__ == "__main__":
    unittest.main()
