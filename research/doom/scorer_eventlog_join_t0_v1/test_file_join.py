import json
import tempfile
import unittest
from pathlib import Path

from file_join import classify_files


def _jsonl(path, rows):
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                    encoding="utf-8")


def _sample(ns, kills):
    return {"scheduled_ns": ns - 2, "sample_started_ns": ns - 1,
            "sample_finished_ns": ns + 1, "start_lateness_ns": 1,
            "missed_periods_before": 0,
            "payload": {"schema": "independent-progress-sample-v2", "sample_ns": ns,
                        "kill_count": kills, "death_count": 0,
                        "episode_finished": False, "player_dead": False,
                        "map_exit": False}, "controller_visible": False}


class RuntimeJsonlJoinTests(unittest.TestCase):
    def test_reads_actual_runtime_jsonl_field_shapes_and_classifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            samples = root / "scorer-samples.jsonl"
            _jsonl(events, [
                {"event": "command", "received_ns": 99, "emit_ns": 99},
                {"event": "accepted", "id": "recover-1", "accepted_ns": 100,
                 "emit_ns": 100},
                {"event": "input_admission", "id": "recover-1", "key": "space",
                 "admitted_ns": 120, "input_ack_ns": 121, "emit_ns": 121},
            ])
            _jsonl(samples, [_sample(110, 0), _sample(130, 1)])
            result = classify_files(events, samples, "recover-1", max_gap_ns=100)
            self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS")
            self.assertEqual(result["positive_sample_ns"], 130)

    def test_missing_runtime_jsonl_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            samples = root / "scorer-samples.jsonl"
            _jsonl(events, [])
            _jsonl(samples, [])
            result = classify_files(events, samples, "recover-1", max_gap_ns=100)
            self.assertEqual(result["decision"], "POST_CANCELLATION_COOCCURRENCE")
            self.assertEqual(result["reason"], "missing_or_ambiguous_acceptance")
            samples.unlink()
            result = classify_files(events, samples, "recover-1", max_gap_ns=100)
            self.assertEqual(result["reason"], "invalid_or_missing_runtime_jsonl")

    def test_malformed_jsonl_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            samples = root / "scorer-samples.jsonl"
            events.write_text("{bad json}\n", encoding="utf-8")
            _jsonl(samples, [_sample(110, 0)])
            result = classify_files(events, samples, "recover-1", max_gap_ns=100)
            self.assertEqual(result["reason"], "invalid_or_missing_runtime_jsonl")


if __name__ == "__main__":
    unittest.main()
