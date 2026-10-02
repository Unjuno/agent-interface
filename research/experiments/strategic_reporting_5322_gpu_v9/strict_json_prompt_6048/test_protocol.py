import json
import unittest

from protocol import build_prompt, make_report, validate_raw


def valid_report():
    return json.dumps({
        "prediction": "INCONCLUSIVE", "confidence": 0.5,
        "unknown_probability": 0.75, "evidence_source": None,
        "missing_evidence": ["sample size"],
        "audit_recommendation": "REQUEST_MORE_DATA",
    })


class ProtocolTests(unittest.TestCase):
    def test_input_is_deterministic_and_prompt_excludes_private_truth(self):
        a = make_report()
        self.assertEqual(a, make_report())
        prompt = build_prompt(a)
        self.assertIn("JSON number", prompt)
        self.assertIn("no Markdown", prompt)
        self.assertNotIn("truth_label", prompt)

    def test_valid_contract(self):
        self.assertEqual(validate_raw(valid_report()), (True, "valid"))

    def test_fence_rejected(self):
        self.assertEqual(validate_raw("```json\n" + valid_report() + "\n```"),
                         (False, "not_one_bare_json_object"))

    def test_numeric_string_rejected(self):
        value = json.loads(valid_report())
        value["confidence"] = "0.5"
        self.assertEqual(validate_raw(json.dumps(value))[0], False)

    def test_boolean_not_accepted_as_number(self):
        value = json.loads(valid_report())
        value["confidence"] = True
        self.assertEqual(validate_raw(json.dumps(value))[0], False)

    def test_nullish_string_source_rejected(self):
        value = json.loads(valid_report())
        value["evidence_source"] = "None"
        self.assertEqual(validate_raw(json.dumps(value))[0], False)

    def test_extra_text_and_extra_key_rejected(self):
        self.assertFalse(validate_raw("Result: " + valid_report())[0])
        value = json.loads(valid_report())
        value["comment"] = "extra"
        self.assertFalse(validate_raw(json.dumps(value))[0])

    def test_duplicate_json_keys_rejected(self):
        raw = '{"prediction":"HIGH","prediction":"LOW"}'
        self.assertEqual(validate_raw(raw), (False, "invalid_json"))

    def test_unhashable_enums_and_nan_rejected_without_crashing(self):
        value = json.loads(valid_report())
        value["prediction"] = []
        self.assertFalse(validate_raw(json.dumps(value))[0])
        value = json.loads(valid_report())
        value["evidence_source"] = []
        self.assertFalse(validate_raw(json.dumps(value))[0])
        value = json.loads(valid_report())
        value["confidence"] = float("nan")
        self.assertFalse(validate_raw(json.dumps(value))[0])


if __name__ == "__main__":
    unittest.main()
