import unittest

from audit import row_emission_errors


class EmissionEvidenceTests(unittest.TestCase):
    def test_literal_false_is_accepted(self):
        self.assertEqual(row_emission_errors({"physical_input_emitted": False}), [])

    def test_missing_field_is_not_silently_false(self):
        self.assertEqual(row_emission_errors({}), ["physical_input_emitted_missing"])

    def test_true_field_is_rejected(self):
        self.assertEqual(row_emission_errors({"physical_input_emitted": True}),
                         ["physical_input_emitted_not_false"])

    def test_integer_zero_is_not_a_boolean_receipt(self):
        self.assertEqual(row_emission_errors({"physical_input_emitted": 0}),
                         ["physical_input_emitted_not_false"])


if __name__ == "__main__":
    unittest.main()

