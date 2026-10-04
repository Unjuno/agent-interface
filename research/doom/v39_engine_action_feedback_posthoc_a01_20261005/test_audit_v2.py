"""Eight-field saved-result regression controls; never run the producer."""
import copy
import json
import unittest

import audit
import audit_v2


class RepairedDerivedFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = audit.pinned_inputs()
        cls.result = json.loads((audit.HERE / "RESULT.json").read_text(encoding="utf-8"))

    def mutated_pair(self, field, value, censored=False):
        result = copy.deepcopy(self.result)
        pair = next(p for cell in result["cells"] for p in cell["pairs"]
                    if p["neutral_observation_censored_at_window_end"] is censored)
        pair[field] = value
        return result

    def assert_rejected(self, result):
        with self.assertRaises(ValueError):
            audit_v2.audit_result(self.inputs, result)

    def test_pristine_saved_result_passes_without_mutation(self):
        before_result = copy.deepcopy(self.result)
        before_inputs = dict(self.inputs)
        checked = audit_v2.audit_result(self.inputs, self.result)
        self.assertEqual(checked["decision"], "PASS_RAW_RECONSTRUCTION_INTEGRITY")
        self.assertEqual(checked["pulse_pairs"], 6)
        self.assertEqual(checked["neutral_observation_censored_pairs"], 1)
        self.assertEqual(self.inputs, before_inputs)
        self.assertEqual(self.result, before_result)

    def test_mutated_pair_key_is_rejected(self):
        self.assert_rejected(self.mutated_pair("key", "SPACE"))

    def test_mutated_move_right_summary_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["summary"]["all_pulse_pairs_reported_move_right"] = False
        self.assert_rejected(result)

    def test_mutated_neutral_summary_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["summary"]["all_pairs_observed_neutral_after_verified_up"] = True
        self.assert_rejected(result)

    def test_mutated_positive_count_is_rejected(self):
        self.assert_rejected(self.mutated_pair("positive_samples_before_keyup", 999))

    def test_mutated_scorer_count_is_rejected(self):
        self.assert_rejected(self.mutated_pair("scorer_sample_count", 999))

    def test_mutated_onset_latency_is_rejected(self):
        self.assert_rejected(self.mutated_pair("onset_observation_latency_from_admission_ms", [-99, -88]))

    def test_mutated_neutral_latency_is_rejected(self):
        self.assert_rejected(self.mutated_pair("neutral_observation_latency_from_release_return_ms", [1, 2]))

    def test_mutated_pre_onset_timestamp_is_rejected(self):
        self.assert_rejected(self.mutated_pair("pre_onset_false_sample_returned_ns", None))

    def test_censored_neutral_latency_must_stay_null(self):
        self.assert_rejected(self.mutated_pair("neutral_observation_latency_from_release_return_ms", [0.0, 0.0], censored=True))

    def test_cumulative_window_counts_are_preserved(self):
        pairs = [p for c in self.result["cells"] for p in c["pairs"]]
        self.assertEqual([p["positive_samples_before_keyup"] for p in pairs], [3, 6, 4, 8, 4, 7])
        self.assertEqual([p["scorer_sample_count"] for p in pairs], [17, 17, 16, 16, 18, 18])
        result = copy.deepcopy(self.result)
        # The second 01-pulse hold has three positives of its own, six in the window.
        result["cells"][1]["pairs"][1]["positive_samples_before_keyup"] = 3
        self.assert_rejected(result)

    def test_repaired_fields_reject_missing_values_and_type_aliases(self):
        pair = self.result["cells"][1]["pairs"][0]
        cases = [
            ("positive_samples_before_keyup", float(pair["positive_samples_before_keyup"])),
            ("scorer_sample_count", float(pair["scorer_sample_count"])),
            ("pre_onset_false_sample_returned_ns", float(pair["pre_onset_false_sample_returned_ns"])),
            ("onset_observation_latency_from_admission_ms", tuple(pair["onset_observation_latency_from_admission_ms"])),
            ("neutral_observation_latency_from_release_return_ms", tuple(pair["neutral_observation_latency_from_release_return_ms"])),
        ]
        for field, value in cases:
            with self.subTest(field=field, case="type"):
                self.assert_rejected(self.mutated_pair(field, value))
        for field, value in [("all_pulse_pairs_reported_move_right", 1),
                             ("all_pairs_observed_neutral_after_verified_up", 0)]:
            with self.subTest(field=field, case="boolean alias"):
                result = copy.deepcopy(self.result)
                result["summary"][field] = value
                self.assert_rejected(result)
        fields = ["key", "positive_samples_before_keyup", "scorer_sample_count",
                  "onset_observation_latency_from_admission_ms",
                  "neutral_observation_latency_from_release_return_ms",
                  "pre_onset_false_sample_returned_ns"]
        for field in fields:
            with self.subTest(field=field, case="missing"):
                result = copy.deepcopy(self.result)
                del result["cells"][1]["pairs"][0][field]
                self.assert_rejected(result)
        result = copy.deepcopy(self.result)
        censored = next(p for c in result["cells"] for p in c["pairs"]
                        if p["neutral_observation_censored_at_window_end"])
        del censored["neutral_observation_latency_from_release_return_ms"]
        self.assert_rejected(result)

    def test_existing_latency_error_is_preserved(self):
        result = self.mutated_pair("last_window_sample_minus_release_return_ms", 999999)
        with self.assertRaisesRegex(ValueError, "^last sample/release relation mismatch: 01-pulse$"):
            audit_v2.audit_result(self.inputs, result)

    def test_existing_unverified_release_error_is_preserved(self):
        inputs = dict(self.inputs)
        path = "research/doom/absolute_pair_59_4d74_20261004/05-pulse/runtime/events.jsonl"
        rows = [json.loads(line) for line in inputs[path].splitlines()]
        next(row for row in rows if row.get("event") == "input_release_transition")["owner_transition_verified"] = False
        inputs[path] = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "^key-up is unverified: 05-pulse$"):
            audit_v2.audit_result(inputs, self.result)


if __name__ == "__main__":
    unittest.main()
