"""A15 never delays or reissues model completion responses."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_live import should_delay_completion

class NoDelayTests(unittest.TestCase):
    def test_no_completion_is_delayed(self):
        for turn in range(1, 13):
            self.assertFalse(should_delay_completion("turn/completed", turn))
    def test_noncompletion_is_never_delayed(self):
        self.assertFalse(should_delay_completion("item/started", 1))

if __name__ == "__main__":
    unittest.main()
