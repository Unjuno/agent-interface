"""Regression check against the exact merged #7471 classifier on current main."""
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH_DOOM = HERE.parent
sys.path.insert(0, str(HERE))
from candidate import classify_intent as classify_successor

PRIOR_PATH = RESEARCH_DOOM / "scorer_admission_attribution_t0_v1" / "candidate.py"
SPEC = importlib.util.spec_from_file_location("merged_scorer_admission_t0_candidate", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRIOR)


def _sample(ns, kills):
    return {"sample_started_ns": ns - 1, "sample_finished_ns": ns + 1,
            "missed_periods_before": 0,
            "payload": {"schema": "independent-progress-sample-v2", "sample_ns": ns,
                        "kill_count": kills, "death_count": 0, "map_exit": False}}


class PriorPolicyRegressionTests(unittest.TestCase):
    def test_merged_first_baseline_accepts_pre_input_progress_but_successor_rejects(self):
        samples = [(105, 0), (110, 0), (115, 1), (130, 1)]
        prior = PRIOR.classify_progress(samples, 100, 120, max_gap_ns=100)
        events = [{"event": "accepted", "id": "recover-1", "accepted_ns": 100},
                  {"event": "input_admission", "id": "recover-1", "admitted_ns": 120}]
        receipts = [_sample(ns, kills) for ns, kills in samples]
        successor = classify_successor(events, receipts, "recover-1", max_gap_ns=100)
        self.assertEqual(prior["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertEqual(prior["baseline_ns"], 105)
        self.assertEqual(successor["decision"], "POST_CANCELLATION_COOCCURRENCE")
        self.assertEqual(successor["reason"], "no_bounded_post_input_progress")


if __name__ == "__main__":
    unittest.main()
