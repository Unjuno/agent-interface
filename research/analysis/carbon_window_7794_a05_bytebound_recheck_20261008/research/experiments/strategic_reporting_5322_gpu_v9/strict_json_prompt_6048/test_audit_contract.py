import json
import unittest

from audit import validate_output


class IndependentAuditContractTests(unittest.TestCase):
    def test_rejects_duplicate_keys(self):
        ok, reason = validate_output('{"prediction":"HIGH","prediction":"LOW"}')
        self.assertFalse(ok)
        self.assertEqual(reason, "invalid_json")

    def test_rejects_boolean_confidence(self):
        value = {
            "prediction": "HIGH", "confidence": True, "unknown_probability": 0.2,
            "evidence_source": None, "missing_evidence": [],
            "audit_recommendation": "NO_ACTION",
        }
        self.assertFalse(validate_output(json.dumps(value))[0])

    def test_rejects_nonfinite_confidence(self):
        value = {
            "prediction": "HIGH", "confidence": float("nan"), "unknown_probability": 0.2,
            "evidence_source": None, "missing_evidence": [],
            "audit_recommendation": "NO_ACTION",
        }
        self.assertFalse(validate_output(json.dumps(value))[0])


if __name__ == "__main__":
    unittest.main()
