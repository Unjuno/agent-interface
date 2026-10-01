import unittest
from pathlib import Path

RUNNER = Path(__file__).with_name("map01_recovery_cover_matched_v2_runner_3243_diagnostic.py")


class RetainedTerminalReplayTest(unittest.TestCase):
    def test_retained_wait_helper_present(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("def wait_retained", source)
        self.assertIn("fallback_terminal = session.wait_retained", source)


if __name__ == "__main__":
    unittest.main()
