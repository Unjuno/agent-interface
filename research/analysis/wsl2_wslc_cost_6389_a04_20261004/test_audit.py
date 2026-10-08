from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from audit import parse_test_count


class TestCountTests(unittest.TestCase):
    def test_accepts_unittest_success_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "suite.stderr.log"
            log.write_bytes(b"Ran 205 tests in 1.234s\n\nOK\n")
            self.assertEqual(parse_test_count(log), 205)

    def test_rejects_missing_or_ambiguous_summary(self):
        for content in (b"Ran 2 tests in 0.1s\nFAILED (failures=1)\n",
                        b"Ran 2 tests in 0.1s\nRan 3 tests in 0.2s\nOK\n"):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                log = Path(directory) / "suite.stderr.log"
                log.write_bytes(content)
                with self.assertRaises(ValueError):
                    parse_test_count(log)


if __name__ == "__main__":
    unittest.main()
