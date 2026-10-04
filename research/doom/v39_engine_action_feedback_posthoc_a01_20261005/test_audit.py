import copy
import json
import unittest

import analyze
import audit


class FeedbackAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = analyze.load_inputs()
        cls.result = analyze.build_result(cls.inputs)

    def test_raw_reconstruction_passes_and_reports_censored_release_feedback(self):
        checked = audit.audit_result(self.inputs, self.result)
        self.assertEqual(checked["decision"], "PASS_RAW_RECONSTRUCTION_INTEGRITY")
        self.assertEqual(checked["pulse_pairs"], 6)
        self.assertEqual(checked["neutral_observation_censored_pairs"], 1)
        self.assertEqual(checked["task_effects_observed"], 0)

    def test_unverified_keyup_is_rejected(self):
        mutated = dict(self.inputs)
        path = "research/doom/absolute_pair_59_4d74_20261004/05-pulse/runtime/events.jsonl"
        rows = [json.loads(line) for line in mutated[path].splitlines()]
        release = next(row for row in rows if row.get("event") == "input_release_transition")
        release["owner_transition_verified"] = False
        mutated[path] = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "unverified"):
            audit.audit_result(mutated, self.result)

    def test_missing_engine_positive_is_rejected(self):
        mutated = dict(self.inputs)
        path = "research/doom/absolute_pair_59_4d74_20261004/05-pulse/scorer-last-action.jsonl"
        rows = [json.loads(line) for line in mutated[path].splitlines()]
        for row in rows:
            row["action"][5] = 0.0
        mutated[path] = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "no in-hold engine"):
            audit.audit_result(mutated, self.result)

    def test_non_neutral_state_immediately_before_admission_is_rejected(self):
        mutated = dict(self.inputs)
        path = "research/doom/absolute_pair_59_4d74_20261004/05-pulse/scorer-last-action.jsonl"
        rows = [json.loads(line) for line in mutated[path].splitlines()]
        first_admission = 68857000143
        prior = [row for row in rows if row["sample_returned_ns"] < first_admission]
        prior[-1]["action"][5] = 1.0
        mutated[path] = ("\n".join(json.dumps(row) for row in rows) + "\n").encode()
        with self.assertRaisesRegex(ValueError, "latest pre-admission action sample is not neutral"):
            audit.audit_result(mutated, self.result)

    def test_fabricated_neutral_after_censored_window_is_rejected(self):
        result = copy.deepcopy(self.result)
        pair = next(p for c in result["cells"] for p in c["pairs"]
                    if p["neutral_observation_censored_at_window_end"])
        pair["first_neutral_after_keyup_sample_returned_ns"] = 999
        with self.assertRaisesRegex(ValueError, "censored neutral time was fabricated"):
            audit.audit_result(self.inputs, result)

    def test_mutated_onset_boundary_is_rejected(self):
        result = copy.deepcopy(self.result)
        result["cells"][1]["pairs"][0]["first_positive_sample_started_ns"] += 1
        with self.assertRaisesRegex(ValueError, "first positive sample time mismatch"):
            audit.audit_result(self.inputs, result)


if __name__ == "__main__":
    unittest.main()
