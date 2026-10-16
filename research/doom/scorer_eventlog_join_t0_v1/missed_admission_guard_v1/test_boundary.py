"""Ordinary unit regressions; no historical producer, game, model or input."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from candidate_v2 import classify_intent
from file_join_v2 import classify_files
from runtime_bundle_v2 import classify_run

POLICY = HERE.parent / "runtime_bundle_a01_20261005" / "SOURCE_POLICY.json"
FREEZE = POLICY.with_name("FREEZE.json")
EVENTS = [{"event": "accepted", "id": "recover-1", "accepted_ns": 100},
          {"event": "input_admission", "id": "recover-1", "admitted_ns": 120}]


def sample(ns, kills, missed=0, *, map_exit=False):
    return {"sample_started_ns": ns - 1, "sample_finished_ns": ns + 1,
            "missed_periods_before": missed,
            "payload": {"sample_ns": ns, "kill_count": kills,
                        "death_count": 0, "map_exit": map_exit}}


def classify(samples, *, gap=100):
    return classify_intent(EVENTS, samples, "recover-1", max_gap_ns=gap)


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class AdmissionBoundaryTests(unittest.TestCase):
    def test_missed_period_at_first_input_rejects_later_kill(self):
        result = classify([sample(110, 0), sample(120, 0, 1), sample(130, 1)])
        self.assertEqual(result, {"decision": "POST_CANCELLATION_COOCCURRENCE",
                                  "reason": "missed_scorer_period", "causal_attribution": False})

    def test_missed_period_at_first_input_rejects_later_map_exit(self):
        result = classify([sample(110, 0), sample(120, 0, 1), sample(130, 0, map_exit=True)])
        self.assertEqual(result["reason"], "missed_scorer_period")

    def test_zero_missed_at_first_input_preserves_valid_result(self):
        ordinary = classify([sample(110, 0), sample(130, 1)])
        boundary = classify([sample(110, 0), sample(120, 0), sample(130, 1)])
        self.assertEqual(boundary, ordinary)
        self.assertEqual(boundary["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertEqual((boundary["baseline_ns"], boundary["positive_sample_ns"], boundary["gap_ns"]),
                         (110, 130, 20))

    def test_missed_period_after_input_rejects(self):
        self.assertEqual(classify([sample(110, 0), sample(121, 0, 1), sample(130, 1)])["reason"],
                         "missed_scorer_period")

    def test_missed_period_on_positive_sample_rejects(self):
        self.assertEqual(classify([sample(110, 0), sample(130, 1, 1)])["reason"],
                         "missed_scorer_period")

    def test_missed_period_before_selected_baseline_is_outside_interval(self):
        result = classify([sample(105, 0, 1), sample(110, 0), sample(130, 1)])
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertEqual(result["baseline_ns"], 110)

    def test_missed_period_after_first_positive_does_not_retroactively_reject(self):
        self.assertEqual(classify([sample(110, 0), sample(130, 1), sample(140, 1, 1)])["decision"],
                         "ADMISSION_BRACKETED_PROGRESS")

    def test_exact_gap_accepts_and_exceeded_gap_rejects(self):
        samples = [sample(110, 0), sample(120, 0), sample(130, 1)]
        self.assertEqual(classify(samples, gap=20)["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertEqual(classify(samples, gap=19)["reason"], "positive_sample_gap_exceeded")

    def test_prior_gap_error_precedence_is_preserved(self):
        self.assertEqual(classify([sample(110, 0), sample(131, 1, 1)], gap=20)["reason"],
                         "positive_sample_gap_exceeded")

    def test_preinput_gain_without_new_progress_still_rejects(self):
        self.assertEqual(classify([sample(105, 0), sample(115, 1), sample(120, 1), sample(130, 1)])["reason"],
                         "no_bounded_post_input_progress")

    def test_only_admission_time_gain_is_not_a_postinput_observation(self):
        self.assertEqual(classify([sample(110, 0), sample(120, 1)])["reason"],
                         "no_bounded_post_input_progress")

    def test_missing_baseline_still_rejects(self):
        self.assertEqual(classify([sample(100, 0), sample(120, 0), sample(130, 1)])["reason"],
                         "no_post_acceptance_pre_input_baseline")

    def test_nonmonotonic_or_duplicate_clocks_reject(self):
        for samples in ([sample(110, 0), sample(120, 0), sample(120, 1)],
                        [sample(110, 0), sample(130, 1), sample(120, 0)]):
            with self.subTest(samples=samples):
                self.assertEqual(classify(samples)["reason"], "scorer_clock_not_strictly_increasing")

    def test_invalid_missed_period_types_at_admission_reject(self):
        for missed in (True, -1, 1.0, None):
            with self.subTest(missed=missed):
                result = classify([sample(110, 0), sample(120, 0, missed), sample(130, 1)])
                self.assertEqual(result["reason"], "invalid_scorer_state_or_scheduler")


class CorrectedConsumerTests(unittest.TestCase):
    def make_bundle(self, root, *, missed=1):
        samples = [sample(110, 0), sample(120, 0, missed), sample(130, 1)]
        write_jsonl(root / "events.jsonl", EVENTS)
        write_jsonl(root / "scorer-samples.jsonl", samples)
        sources = json.loads(POLICY.read_text(encoding="utf-8"))["sources"]
        (root / "sources.json").write_text(json.dumps(sources), encoding="utf-8")
        (root / "scorer-summary.json").write_text(json.dumps({
            "schema": "map01-independent-scorer-integration-v3",
            "controller_visible": False, "sample_count": len(samples)}), encoding="utf-8")

    def test_jsonl_consumer_uses_corrected_boundary_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_bundle(root)
            result = classify_files(root / "events.jsonl", root / "scorer-samples.jsonl", "recover-1", max_gap_ns=100)
        self.assertEqual(result["reason"], "missed_scorer_period")

    def test_runtime_directory_consumer_uses_corrected_boundary_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_bundle(root)
            result = classify_run(root, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "missed_scorer_period")

    def test_runtime_directory_zero_missed_case_still_accepts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_bundle(root, missed=0)
            result = classify_run(root, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS")

    def test_runtime_directory_metadata_validation_remains_in_force(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_bundle(root, missed=0)
            (root / "scorer-summary.json").write_text("{}", encoding="utf-8")
            result = classify_run(root, "recover-1", max_gap_ns=100, source_policy=POLICY, freeze=FREEZE)
        self.assertEqual(result["reason"], "invalid_scorer_summary")


if __name__ == "__main__":
    unittest.main()
