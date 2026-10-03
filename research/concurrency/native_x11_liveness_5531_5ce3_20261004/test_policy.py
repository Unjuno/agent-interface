import unittest
from policy import classify

class PolicyTests(unittest.TestCase):
    def test_timeout_is_not_death(self):
        self.assertEqual(classify(True, False, None), 'SUSPECTED_UNAVAILABLE')
    def test_terminal_is_independent(self):
        self.assertEqual(classify(True, True, None), 'FAILED')
    def test_late_valid_clears_only_suspicion(self):
        self.assertEqual(classify(False, False, True, 'SUSPECTED_UNAVAILABLE'), 'RESPONSIVE_SCOPED')
    def test_terminal_absorbing(self):
        self.assertEqual(classify(False, False, True, 'FAILED'), 'FAILED')
    def test_invalid_not_clear(self):
        self.assertEqual(classify(False, False, False), 'EVIDENCE_INVALID')
    def test_no_response(self):
        self.assertEqual(classify(False, False, None), 'UNKNOWN')

if __name__ == '__main__': unittest.main()
