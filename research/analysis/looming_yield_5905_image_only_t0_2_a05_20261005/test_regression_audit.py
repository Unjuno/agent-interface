"""Independent raw-image audit detects screen-score and threshold mutations."""

import unittest

import audit
from candidate import analyze
from regression_estimator import estimate_ttc
from test_candidate import approach


def screen_for(sequence):
    source = analyze(sequence)
    times = [frame["t_s"] for frame in sequence["frames"]]
    radii = [frame["radius_px"] for frame in source["frames"]]
    estimate = estimate_ttc(times, radii) if source["status"] == "TRACKABLE" else None
    thresholds = (1.5, 2.0, 2.5, 2.8, 3.0, 4.0)
    return {"per_sequence": {sequence["sequence_id"]: {
            "status": source["status"], "reason": source["reason"],
            "secant_ttc_s": source["metrics"].get("secant_ttc_s"),
            "regression_ttc_s": estimate,
            "secant_grid": source["ttc_grid"],
            "pixel_grid": source["pixel_grid"],
            "growth_grid": source["growth_grid"],
        "regression_grid": {str(limit): bool(
            source["status"] == "TRACKABLE" and estimate is not None and
            0.20 < estimate <= limit) for limit in thresholds},
    }}}


class RegressionAuditTests(unittest.TestCase):
    def test_raw_reconstruction_matches_all_frame_estimate(self):
        sequence = approach("fixture-1", radii=(7, 8, 9, 10, 11))
        screen = screen_for(sequence)
        screen["per_sequence"]["fixture-1"].update({
            "pixel_grid": analyze(sequence)["pixel_grid"],
            "growth_grid": analyze(sequence)["growth_grid"],
            "secant_grid": analyze(sequence)["ttc_grid"],
        })
        self.assertTrue(callable(getattr(audit, "audit_regression", None)))
        truth = {"contact_cases": {"fixture-1": {"contact_at_s": 5.0}},
                 "control_labels": {}}
        report = audit.audit_regression({"sequences": [sequence]}, truth, screen)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["checked_sequences"], 1)

    def test_auditor_rejects_tampered_regression_estimate(self):
        sequence = approach("fixture-1", radii=(7, 8, 9, 10, 11))
        screen = screen_for(sequence)
        screen["per_sequence"]["fixture-1"].update({
            "pixel_grid": analyze(sequence)["pixel_grid"],
            "growth_grid": analyze(sequence)["growth_grid"],
            "secant_grid": analyze(sequence)["ttc_grid"],
        })
        self.assertTrue(callable(getattr(audit, "audit_regression", None)))
        screen["per_sequence"]["fixture-1"]["regression_ttc_s"] = 99.0
        truth = {"contact_cases": {"fixture-1": {"contact_at_s": 5.0}},
                 "control_labels": {}}
        report = audit.audit_regression({"sequences": [sequence]}, truth, screen)
        self.assertIn("regression_ttc:fixture-1", report["errors"])


if __name__ == "__main__":
    unittest.main()
