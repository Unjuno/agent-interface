import asyncio
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import candidate

class DeadlineConstruction(unittest.TestCase):
    def test_expired_and_equal_deadline_refuse(self):
        self.assertIs(candidate.deadline_valid(100, 100), False)
        self.assertIs(candidate.deadline_valid(101, 100), False)

    def test_fresh_deadline_preserved(self):
        self.assertIs(candidate.deadline_valid(99, 100), True)

    def test_actual_guard_refuses_delayed_value_and_cleans_up(self):
        row = asyncio.run(candidate.condition('shield_deadline', 'decision_delay', False))
        self.assertEqual(row['timed']['terminal'], 'value')
        self.assertGreaterEqual(row['timed']['decision_ns'], row['deadline_ns'])
        self.assertIs(row['timed']['accepted'], False)
        self.assertIs(row['companion']['accepted'], True)
        self.assertIs(row['all_tasks_terminal'], True)

if __name__ == '__main__':
    unittest.main()
