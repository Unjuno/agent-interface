from pathlib import Path
import unittest


class FullGoldenIpcRunnerTest(unittest.TestCase):
    def test_runner_is_scoped_and_non_authoritative(self):
        source = Path(__file__).with_name("run_full_golden_ipc_v1.py").read_text()
        self.assertIn("container-host-shared-volume-ipc", source)
        self.assertIn('"authority_granted": False', source)
        self.assertIn("len(rows) == 6", source)


if __name__ == "__main__":
    unittest.main()
