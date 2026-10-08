import unittest
from pathlib import Path

ROOT = Path(__file__).parent


class T2cConstructionTests(unittest.TestCase):
    def test_runner_observes_app_events_at_actual_tk_output_path(self):
        source = (ROOT / "runner_v3.py").read_text(encoding="utf-8")
        self.assertIn('tk_out = out / "tk"', source)
        self.assertIn('app_path = tk_out / "app_events.jsonl"', source)
        self.assertIn('str(tk_out)', source)

    def test_candidate_reads_same_nested_tk_event_stream(self):
        source = (ROOT / "candidate_v3.py").read_text(encoding="utf-8")
        self.assertIn('trace / "tk" / "app_events.jsonl"', source)
        self.assertIn('trace / "observer_events.jsonl"', source)

    def test_candidate_v3_refuses_reusing_run_artifacts(self):
        source = (ROOT / "candidate_v3.py").read_text(encoding="utf-8")
        self.assertIn('RUN_DIR.exists()', source)
        self.assertIn('candidate.v3.raw.json', source)
        self.assertIn('do not rerun', source)


if __name__ == "__main__":
    unittest.main()
