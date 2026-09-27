from pathlib import Path
import unittest


class FullGoldenIpcV2Test(unittest.TestCase):
    def test_runner_has_first_stop_and_hash_gate(self):
        source = Path(__file__).with_name("run_full_golden_ipc_v2.py").read_text()
        self.assertIn("STOP_SOURCE_HASH_MISMATCH", source)
        self.assertIn("first_terminal_stop", source)
        self.assertIn("retry_count", source)
        self.assertIn("write_report(args.out, report)", source)


if __name__ == "__main__":
    unittest.main()
