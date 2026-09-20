import unittest
import hashlib

import torch
from torch.nn import functional as F

import audit


class FullCovariateAuditTests(unittest.TestCase):
    def test_each_of_six_columns_is_bound(self):
        expected = [.1, .02, -.03, .01, .90, 1.0]
        for column in range(6):
            with self.subTest(column=column):
                changed = expected.copy()
                changed[column] += .01
                self.assertIn(f"feature_{column}_mismatch", audit.compare_vector(changed, expected))

    def test_exact_six_feature_vector_passes(self):
        row = [.1, .02, -.03, .01, .90, 1.0]
        self.assertEqual(audit.compare_vector(row, row), [])

    def test_wrong_width_fails_closed(self):
        self.assertEqual(audit.compare_vector([.1] * 5, [.1] * 6), ["feature_width"])

    def test_nan_fails_closed(self):
        self.assertIn("feature_4_mismatch", audit.compare_vector([.1, .02, -.03, .01, float("nan"), 1.0],
                                                                  [.1, .02, -.03, .01, .9, 1.0]))

    def test_shifted_confidence_visibility_bounds(self):
        valid = [.1, -.05, .02, -.01, .9, 1.0]
        self.assertTrue(.80 <= valid[4] <= 1.00 and valid[5] == 1.0)
        for invalid_confidence in (.799, 1.001):
            self.assertFalse(.80 <= invalid_confidence <= 1.00)
        self.assertNotEqual(0.0, valid[5])

    def test_generator_seed_is_deterministic_and_preserves_all_six(self):
        a = audit.shifted_class(1, 64, 3568).tolist()
        b = audit.shifted_class(1, 64, 3568).tolist()
        self.assertEqual(a, b)
        for row in a:
            self.assertTrue(.071 <= abs(row[0]) <= .149)
            self.assertLessEqual(abs(row[1]), .10)
            self.assertLessEqual(abs(row[2]), .05)
            self.assertLessEqual(abs(row[3]), .05)
            self.assertTrue(.80 <= row[4] <= 1.0)
            self.assertEqual(row[5], 1.0)

    def test_model_forward_matches_independent_linear_reference(self):
        torch.manual_seed(3892)
        state = {}
        for layer, shape in ((0, (16, 6)), (2, (16, 16)), (4, (3, 16))):
            for param, value_shape in (("weight", shape), ("bias", (shape[0],))):
                values = torch.randn(value_shape, dtype=torch.float32)
                state[f"net.{layer}.{param}"] = {"shape": list(value_shape), "values": values.flatten().tolist()}
        tensors = audit.state_tensors(state)
        features = audit.balanced_class(1, 12, 3999).tolist()
        actual = audit.forward(features, tensors)
        x = torch.tensor(features, dtype=torch.float32)
        for layer in (0, 2, 4):
            x = F.linear(x, tensors[f"net.{layer}.weight"], tensors[f"net.{layer}.bias"])
            if layer != 4:
                x = torch.tanh(x)
        self.assertEqual(actual, x.argmax(-1).tolist())

    def test_git_blob_identity_uses_exact_bytes(self):
        raw = b"bounded evidence\n"
        expected = hashlib.sha1(b"blob 17\0" + raw).hexdigest()
        self.assertEqual(audit.git_blob_sha1(raw), expected)

    def test_checkout_newline_normalization(self):
        self.assertEqual(audit.canonical_result_bytes(b"raw result\r\n"), b"raw result\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
