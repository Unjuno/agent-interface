import unittest

from audit import NAMES, validate


class HarnessTests(unittest.TestCase):
    def test_exact_seven_case_roster(self):
        self.assertEqual(len(NAMES), 7)
        self.assertEqual(NAMES[0], "exit-0")
        self.assertEqual(NAMES[-1], "sorted-once")

    def test_empty_record_fails_closed(self):
        self.assertTrue(validate({}))

    def test_every_broker_case_is_one_shot(self):
        from pathlib import Path
        from runner import broker_command
        command = broker_command(Path("/tmp/ipc"), "/out/case")
        self.assertEqual(command[-1], "--once")
        self.assertEqual(command.count("--once"), 1)


if __name__ == "__main__":
    unittest.main()

