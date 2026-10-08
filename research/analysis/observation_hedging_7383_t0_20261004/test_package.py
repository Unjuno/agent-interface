"""Construction tests; formal candidate/auditor invocations are separate."""
import json
import unittest
from pathlib import Path

from . import auditor, candidate


HERE = Path(__file__).resolve().parent


class HedgingT0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((HERE / "spec.json").read_text())
        cls.result = candidate.run(cls.spec)

    def test_frozen_calibration_and_denominators(self):
        self.assertEqual(self.result["hedge_threshold_ms"], 6)
        self.assertEqual(len(self.result["rows"]), 1000)
        self.assertEqual({c: sum(r["condition"] == c for r in self.result["rows"]) for c in self.spec["conditions"]}, {c: 200 for c in self.spec["conditions"]})

    def test_heavy_tail_useful_region_and_no_work_or_deadline_regression(self):
        summary = self.result["summaries"]["iid_heavy_tail"]
        single, hedge = summary["single"], summary["delayed_hedge"]
        self.assertGreaterEqual((single["p95_ms"] - hedge["p95_ms"]) / single["p95_ms"], 0.10)
        self.assertLessEqual(hedge["delayed_duplicate_work_ratio"], 1.20)
        self.assertLessEqual(hedge["deadline_misses"], single["deadline_misses"])

    def test_correlated_and_shared_queue_are_not_misrepresented_as_iid_gain(self):
        for condition in ("correlated_tail", "shared_queue_saturation"):
            arms = self.result["summaries"][condition]
            self.assertGreaterEqual(arms["delayed_hedge"]["p95_ms"], arms["single"]["p95_ms"])

    def test_generation_change_accepts_only_current_generation(self):
        group = [r for r in self.result["rows"] if r["condition"] == "generation_between_captures"]
        for row in group:
            delayed = row["arms"]["delayed_hedge"]
            decision = delayed["consumer"]
            if decision["disposition"] == "ADMIT":
                accepted = next(x for x in delayed["requests"] if x["request_id"] == decision["admitted_request_ids"][0])
                self.assertTrue(accepted["complete"])
                self.assertEqual(accepted["capture_epoch"], decision["current_epoch"])
        self.assertGreater(sum(r["arms"]["single"]["consumer"]["disposition"] == "YIELD" for r in group), 0)

    def test_independent_auditor_reconstructs_candidate(self):
        checked = auditor.validate(self.spec, self.result)
        self.assertEqual(checked["disposition"], "PASS_METHOD_SCOPED")
        self.assertEqual(checked["checks"]["rows_reconstructed"], 1000)

    def test_all_four_corruptions_are_rejected(self):
        controls = auditor.mutations(self.spec, self.result)
        self.assertEqual(len(controls), 4)
        self.assertTrue(all(x["rejected"] for x in controls))


if __name__ == "__main__":
    unittest.main()
