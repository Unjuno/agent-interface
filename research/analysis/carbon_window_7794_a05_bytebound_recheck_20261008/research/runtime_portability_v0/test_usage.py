import copy
import json
import unittest
from pathlib import Path

from usage import UsageError, comparison_eligible, normalized_usage, validate_usage_record

HERE = Path(__file__).resolve().parent


class UsageTests(unittest.TestCase):
    def fixture(self):
        return json.loads((HERE / "retained_usage_fixture.json").read_text(encoding="utf-8"))

    def test_retained_exact_usage_is_accepted(self):
        row = validate_usage_record(self.fixture())
        self.assertEqual(row["usage"]["input_tokens"], 27892)
        self.assertTrue(row["correct"])

    def test_normalized_usage_keeps_exact_source_label(self):
        result = normalized_usage(self.fixture())
        self.assertEqual(result["token_source"], "provider_usage")
        self.assertAlmostEqual(result["input_tokens_per_successful_task"], 27892 / 6)

    def test_proxy_cannot_fabricate_tokens(self):
        row = self.fixture()
        row["token_source"] = "proxy_only"
        with self.assertRaises(UsageError):
            validate_usage_record(row)

    def test_comparison_requires_matched_model_task_environment_correctness(self):
        left = self.fixture()
        right = copy.deepcopy(left)
        eligible, reasons = comparison_eligible(left, right)
        self.assertTrue(eligible, reasons)
        right["task_set_id"] = "different"
        eligible, reasons = comparison_eligible(left, right)
        self.assertFalse(eligible)
        self.assertIn("mismatch:task_set_id", reasons)

    def test_comparison_rejects_proxy(self):
        left = self.fixture()
        right = copy.deepcopy(left)
        right["token_source"] = "proxy_only"
        right["usage"] = {k: 0 for k in right["usage"]}
        eligible, reasons = comparison_eligible(left, right)
        self.assertFalse(eligible)
        self.assertIn("exact_provider_usage_required", reasons)


if __name__ == "__main__":
    unittest.main()
