"""Local regression for A36's file-backed app-event transport."""
import importlib.util
import tempfile
import time
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("a36_candidate", HERE / "candidate.py")
CANDIDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CANDIDATE)


class CandidateAppEventLogTests(unittest.TestCase):
    def test_reads_a_complete_jsonl_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            path.write_text('{"event":"app_ready","window_id":17}\n',
                            encoding="utf-8")
            result = CANDIDATE.read_app_message(
                path, 0, time.perf_counter_ns() + 100_000_000)
        self.assertEqual(result, {"event": "app_ready", "window_id": 17})

    def test_preserves_an_unparseable_line_as_diagnostic_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            path.write_text("Xlib warning\n", encoding="utf-8")
            result = CANDIDATE.read_app_message(
                path, 0, time.perf_counter_ns() + 100_000_000)
        self.assertEqual(result["event"], "app_event_decode_error")
        self.assertEqual(result["raw_line"], "Xlib warning")
        self.assertTrue(result["error"].startswith("JSONDecodeError:"))


if __name__ == "__main__":
    unittest.main()
