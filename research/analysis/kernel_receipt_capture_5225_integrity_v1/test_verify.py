import hashlib
import unittest
from verify import matrix_check


class ByteBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.raw = b'{\n  "effect": true\n}\n'
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.old = hashlib.sha256(self.raw.replace(b'\n', b'\r\n')).hexdigest()

    def test_exact_serialization(self):
        row = matrix_check(self.raw, self.sha, self.old)
        self.assertTrue(row['historical_crlf_matches'])
        self.assertFalse(row['historical_exact_git_match'])

    def test_semantic_corruption_refused(self):
        self.assertFalse(matrix_check(self.raw.replace(b'true', b'null'), self.sha, self.old)['historical_crlf_matches'])

    def test_equal_json_different_spacing_refused(self):
        self.assertFalse(matrix_check(self.raw.replace(b'  ', b' '), self.sha, self.old)['canonical_lf_matches'])

    def test_crlf_input_not_reinterpreted(self):
        self.assertFalse(matrix_check(self.raw.replace(b'\n', b'\r\n'), self.sha, self.old)['canonical_lf_matches'])

    def test_wrong_historical_pin_refused(self):
        self.assertFalse(matrix_check(self.raw, self.sha, '0' * 64)['historical_crlf_matches'])

    def test_missing_final_newline_refused(self):
        self.assertFalse(matrix_check(self.raw[:-1], self.sha, self.old)['canonical_lf_matches'])


if __name__ == '__main__':
    unittest.main()
