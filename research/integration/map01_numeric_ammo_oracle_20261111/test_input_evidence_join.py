import json
import tempfile
import unittest
from pathlib import Path

from input_evidence_join import join_w_input_samples, load_held_input_evidence


class HeldInputEvidenceJoinTests(unittest.TestCase):
    def test_join_keeps_resolver_and_expiry_provenance_separate(self):
        joined = join_w_input_samples({
            "samples": [{"action_status": "running", "w_key_down": True}],
            "terminal_w_down": False, "claim": "resolver-poll",
        }, {
            "samples": [{"after_ns": 10, "w_key_down": True}],
            "status": "verified", "lease_deadline_ns": 9,
        })
        self.assertEqual(joined["classification"], "BOTH_PRESENT")
        self.assertNotEqual(joined["resolver"]["samples"],
                            joined["expiry_sampler"]["samples"])
        self.assertEqual(joined["resolver"]["claim"], "resolver-poll")

    def test_join_missing_reports_remains_explicit(self):
        joined = join_w_input_samples(None, None)
        self.assertEqual(joined["classification"], "BOTH_MISSING")
        self.assertIsNone(joined["resolver"]["sample_count"])
        self.assertIsNone(joined["expiry_sampler"]["sample_count"])

    def test_missing_resolver_falls_back_to_expiry_samples_without_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            (trial / "expiry-boundary-key-samples.json").write_text(
                json.dumps({"samples": [
                    {"monotonic_after_ns": 12, "w_key_down": True},
                    {"monotonic_after_ns": 13, "w_key_down": False},
                ]}), encoding="utf-8")
            held, join = load_held_input_evidence(trial)

        self.assertEqual(join["source"], "independent-expiry-sampler")
        self.assertEqual(join["classification"], "MISSING_RESOLVER_SAMPLES")
        self.assertEqual(join["sample_count"], 2)
        self.assertIsNone(held["terminal_w_down"])
        self.assertIsNone(held["observed_w_down_before_terminal"])
        self.assertEqual(held["samples"][0]["action_status"], "not_sampled_by_resolver")

    def test_missing_both_files_is_unknown_without_raising(self):
        with tempfile.TemporaryDirectory() as directory:
            held, join = load_held_input_evidence(Path(directory))

        self.assertEqual(join["classification"], "MISSING_RESOLVER_SAMPLES")
        self.assertEqual(held["samples"], [])
        self.assertIsNone(held["terminal_w_down"])
        self.assertIsNone(held["observed_w_down_before_terminal"])

    def test_existing_resolver_receipt_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            expected = {"samples": [{"w_key_down": True}],
                        "terminal_w_down": False, "claim": "resolver poll"}
            (trial / "expiry-held-w-samples.json").write_text(
                json.dumps(expected), encoding="utf-8")
            held, join = load_held_input_evidence(trial)

        self.assertEqual(held, expected)
        self.assertEqual(join["source"], "pending-resolver-poll-samples")
        self.assertEqual(join["classification"], "RESOLVER_SAMPLES_PRESENT")

    def test_invalid_resolver_json_does_not_promote_expiry_samples(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            (trial / "expiry-held-w-samples.json").write_text("{", encoding="utf-8")
            (trial / "expiry-boundary-key-samples.json").write_text(
                json.dumps({"samples": [{"monotonic_after_ns": 12,
                    "w_key_down": True}]}),
                encoding="utf-8")
            held, join = load_held_input_evidence(trial)

        self.assertEqual(join["classification"], "RESOLVER_ARTIFACT_INVALID")
        self.assertEqual(held["samples"], [])
        self.assertIsNone(held["terminal_w_down"])
        self.assertEqual(join["resolver_error"], "JSONDecodeError")

    def test_invalid_expiry_rows_are_not_coerced(self):
        with tempfile.TemporaryDirectory() as directory:
            trial = Path(directory)
            (trial / "expiry-boundary-key-samples.json").write_text(
                json.dumps({"samples": [{"after_ns": "12", "w_key_down": 1}]}),
                encoding="utf-8")
            held, join = load_held_input_evidence(trial)

        self.assertEqual(join["classification"], "EXPIRY_SAMPLER_INVALID")
        self.assertEqual(held["samples"], [])
        self.assertIsNone(held["terminal_w_down"])


if __name__ == "__main__":
    unittest.main()
