import unittest
from audit import audit

class TerminalSyncTests(unittest.TestCase):
    def test_exactly_one_terminal_passes(self):
        rows=[{"event":"cancel_requested","id":"x"},{"event":"input_release_unverified","id":"x"},{"event":"terminal","id":"x"}]
        self.assertEqual(audit(rows,"x")["decision"],"PASS_TERMINAL_EVENT_ONCE")
    def test_missing_terminal_fails(self):
        self.assertEqual(audit([{"event":"cancel_requested","id":"x"}],"x")["decision"],"FAIL_TERMINAL_EVENT_PROTOCOL")
    def test_duplicate_terminal_fails(self):
        rows=[{"event":"terminal","id":"x"},{"event":"terminal","id":"x"}]
        self.assertEqual(audit(rows,"x")["decision"],"FAIL_TERMINAL_EVENT_PROTOCOL")

if __name__=="__main__":
    unittest.main()
