"""Saved-file regressions only; never imports or runs a producer/candidate."""
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
MODULE = Path(os.environ.get("SCORER_AUDIT_MODULE", HERE / "audit.py"))
REPO = Path(os.environ.get("SCORER_FIXTURE_REPO", HERE.parents[3]))
PACKAGE = Path("research/doom/scorer_eventlog_join_t0_v1")


def load_auditor():
    spec = importlib.util.spec_from_file_location("saved_history_auditor_under_test", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SavedHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        paths = [PACKAGE / name for name in ("followup_raw.json", "followup_run.py", "FOLLOWUP.json", "candidate.py", "followup_audit.py")]
        paths.append(Path("research/doom/scorer_admission_attribution_t0_v1/candidate.py"))
        for relative in paths:
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / relative, target)
        self.root = self.repo / PACKAGE
        self.module = load_auditor()
        self.module.ROOT = self.root
        self.raw_path = self.root / "followup_raw.json"
        self.raw = json.loads(self.raw_path.read_text())

    def write_raw(self):
        self.raw_path.write_text(json.dumps(self.raw, indent=2) + "\n")

    def assert_rejected(self):
        result = self.module.audit()
        self.assertFalse(result["pass"], result)
        self.assertTrue(result["errors"], result)

    def test_unchanged_saved_packet_passes(self):
        self.assertTrue(self.module.audit()["pass"])

    def test_baseline_and_zero_delta_are_derived(self):
        result = self.module.audit()
        self.assertEqual(result.get("derived", {}).get("successor_baseline"), [115, 1])
        self.assertEqual(result.get("derived", {}).get("successor_decision"), "POST_CANCELLATION_COOCCURRENCE")
        self.assertEqual(result.get("derived", {}).get("post_input_deltas"), [[130, 0]])

    def test_missing_history_rejected_with_labels_unchanged(self):
        del self.raw["sample_history"]
        self.write_raw()
        self.assert_rejected()

    def test_new_post_input_progress_rejected_with_labels_unchanged(self):
        self.raw["sample_history"][-1][1] = 2
        self.write_raw()
        self.assert_rejected()

    def test_removed_pre_input_progress_rejected_with_labels_unchanged(self):
        self.raw["sample_history"][2][1] = 0
        self.write_raw()
        self.assert_rejected()

    def test_nonmonotonic_history_rejected(self):
        self.raw["sample_history"].reverse()
        self.write_raw()
        self.assert_rejected()

    def test_source_fixture_change_rejected(self):
        source = self.root / "followup_run.py"
        source.write_text(source.read_text().replace("accepted_ns\": 100", "accepted_ns\": 101"))
        self.assert_rejected()

    def test_semantic_layer_rejects_changed_progress_even_with_rebound_raw_pin(self):
        # Counterfactual unit control only: rebind this copy's raw identity so
        # a checksum rejection cannot disguise a missing semantic comparison.
        # The production audit keeps all exact-source pins unchanged.
        self.raw["sample_history"][-1][1] = 2
        self.write_raw()
        content = self.raw_path.read_bytes()
        self.module.PINS["followup_raw.json"] = (
            hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest(),
            hashlib.sha256(content).hexdigest())
        result = self.module.audit()
        self.assertFalse(result["pass"])
        self.assertIn("derived_mismatch:successor_decision", result["errors"])
        self.assertEqual(result["derived"]["successor_decision"], "ADMISSION_BRACKETED_PROGRESS")

    def test_semantic_layer_rejects_wrong_label_even_with_rebound_raw_pin(self):
        self.raw["successor_decision"] = "ADMISSION_BRACKETED_PROGRESS"
        self.write_raw()
        content = self.raw_path.read_bytes()
        self.module.PINS["followup_raw.json"] = (
            hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest(),
            hashlib.sha256(content).hexdigest())
        result = self.module.audit()
        self.assertFalse(result["pass"])
        self.assertIn("derived_mismatch:successor_decision", result["errors"])
        self.assertEqual(result["derived"]["successor_decision"], "POST_CANCELLATION_COOCCURRENCE")

    def test_retained_label_change_rejected(self):
        self.raw["successor_decision"] = "ADMISSION_BRACKETED_PROGRESS"
        self.write_raw()
        self.assert_rejected()


class ReducerTests(unittest.TestCase):
    def setUp(self):
        self.module = load_auditor()

    def reduce(self, history, accepted=100, first_input=120, gap=100, missed=0):
        method = getattr(self.module, "recompute_history", None)
        self.assertTrue(callable(method), "independent raw-history reducer is absent")
        return method(history, accepted, first_input, max_gap_ns=gap, missed_periods=missed)

    def test_current_history_uses_freshest_state(self):
        result = self.reduce([[105, 0], [110, 0], [115, 1], [130, 1]])
        self.assertEqual(result["baseline"], [115, 1])
        self.assertEqual(result["decision"], "POST_CANCELLATION_COOCCURRENCE")

    def test_new_post_input_gain_changes_decision(self):
        result = self.reduce([[105, 0], [115, 1], [130, 2]])
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertEqual(result["positive_sample"], [130, 2])
        self.assertEqual(result["gap_ns"], 15)

    def test_arbitrary_nonzero_baseline_is_supported(self):
        self.assertEqual(self.reduce([[110, 7], [130, 8]])["decision"], "ADMISSION_BRACKETED_PROGRESS")

    def test_pre_input_gain_alone_is_not_progress(self):
        self.assertEqual(self.reduce([[105, 0], [115, 1]])["decision"], "POST_CANCELLATION_COOCCURRENCE")

    def test_missing_baseline_rejects(self):
        self.assertEqual(self.reduce([[99, 0], [130, 1]])["decision"], "POST_CANCELLATION_COOCCURRENCE")

    def test_gap_and_missed_period_reject(self):
        for kwargs in ({"gap": 19}, {"missed": 1}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.reduce([[110, 0], [130, 1]], **kwargs)["decision"], "POST_CANCELLATION_COOCCURRENCE")

    def test_malformed_and_clock_boundaries_fail_closed(self):
        histories = (None, [], [[True, 0], [130, 1]], [[110, False], [130, 1]],
                     [[110, -1], [130, 1]], [[110, 0], [110, 1]], [[130, 1], [110, 0]],
                     [[110, 0], [130, float("nan")]], [[110, 0, 0], [130, 1]])
        for history in histories:
            with self.subTest(history=history):
                self.assertEqual(self.reduce(history)["decision"], "POST_CANCELLATION_COOCCURRENCE")


if __name__ == "__main__":
    unittest.main()
