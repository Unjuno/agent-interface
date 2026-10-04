"""Ordinary inert regressions for A02 validation + corrected admission policy."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

import file_join
import test_file_join_bundle as fixtures


class RunBundleAdmissionGuardTests(unittest.TestCase):
    def setUp(self):
        self.bundle = fixtures.RuntimeBundleJoinTests()
        self.addCleanup(self.bundle.tearDown)
        self.bundle.setUp()

    def _write(self, *, missed_at=120, gain="kill", gain_ns=130,
               include_later=True):
        times = [110, 120] + ([130] if include_later else [])
        if missed_at == 140:
            times.append(140)
        samples = [fixtures._sample(ns, int(gain == "kill" and ns >= gain_ns))
                   for ns in times]
        for row in samples:
            ns = row["payload"]["sample_ns"]
            row["missed_periods_before"] = int(ns == missed_at)
            if gain == "exit" and ns >= gain_ns:
                row["payload"].update(episode_finished=True, map_exit=True)
        if gain == "kill":
            before, after = {"kill_count": 0}, {"kill_count": 1, "delta": 1}
            kind = "KILL_COUNT_INCREASE"
        else:
            before = {"map_exit": False, "episode_finished": False}
            after = {"map_exit": True, "episode_finished": True}
            kind = "MAP_EXIT"
        score_events = [{
            "schema": "independent-progress-event-v2", "event_sequence": 1,
            "observed_ns": gain_ns, "kind": kind, "polarity": "positive",
            "useful": True, "controller_visible": False,
            "before": before, "after": after,
        }]
        self.bundle._write_progress_rows(samples, score_events)
        path = self.bundle.run_dir / "scorer-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["scheduler"]["missed_sample_periods"] = sum(
            row["missed_periods_before"] for row in samples)
        fixtures._json(path, summary)
        # Reconcile the exact complete bundle before testing classification.
        # Failure must come from the policy, not malformed fixture sidecars.
        file_join._validate_bundle(self.bundle.run_dir, self.bundle.research)

    def _assert_missed(self, result):
        self.assertEqual(result["decision"], "POST_CANCELLATION_COOCCURRENCE", result)
        self.assertEqual(result["reason"], "missed_scorer_period", result)
        self.assertIs(result["causal_attribution"], False)

    def test_complete_bundle_rejects_missed_admission_before_kill(self):
        self._write()
        self._assert_missed(self.bundle._classify())

    def test_complete_bundle_rejects_missed_admission_before_map_exit(self):
        self._write(gain="exit")
        self._assert_missed(self.bundle._classify())

    def test_directory_cli_selects_corrected_classifier(self):
        self._write()
        result = subprocess.run([
            sys.executable, str(Path(file_join.__file__).resolve()),
            "--run-dir", str(self.bundle.run_dir), "--research-root",
            str(self.bundle.research), "--intent-id", "recover-1",
            "--max-gap-ns", "100",
        ], check=True, capture_output=True, text=True)
        self.assertEqual(result.stderr, "")
        self._assert_missed(json.loads(result.stdout))

    def test_two_path_helper_selects_corrected_classifier(self):
        self._write()
        self._assert_missed(file_join.classify_files(
            self.bundle.run_dir / "events.jsonl",
            self.bundle.run_dir / "scorer-samples.jsonl", "recover-1",
            max_gap_ns=100))

    def test_zero_missed_admission_preserves_later_kill(self):
        self._write(missed_at=None)
        result = self.bundle._classify()
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS", result)
        self.assertEqual(result["positive_sample_ns"], 130)
        self.assertIs(result["causal_attribution"], False)

    def test_zero_missed_admission_preserves_later_map_exit(self):
        self._write(missed_at=None, gain="exit")
        result = self.bundle._classify()
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS", result)
        self.assertIs(result["causal_attribution"], False)

    def test_admission_only_gain_is_not_post_input_progress(self):
        self._write(missed_at=None, gain_ns=120, include_later=False)
        result = self.bundle._classify()
        self.assertEqual(result["reason"], "no_bounded_post_input_progress", result)

    def test_miss_after_first_positive_does_not_expand_join_interval(self):
        self._write(missed_at=140)
        result = self.bundle._classify()
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS", result)
        self.assertEqual(result["positive_sample_ns"], 130)

    def test_miss_at_selected_baseline_does_not_expand_join_interval(self):
        self._write(missed_at=110)
        result = self.bundle._classify()
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS", result)
        self.assertEqual(result["baseline_ns"], 110)

    def test_existing_gap_rejection_is_preserved(self):
        self._write(missed_at=None)
        result = file_join.classify_run_dir(self.bundle.run_dir, "recover-1",
                                            max_gap_ns=10,
                                            research_root=self.bundle.research)
        self.assertEqual(result["reason"], "positive_sample_gap_exceeded", result)


if __name__ == "__main__":
    unittest.main()
