import hashlib
import io
import json
import statistics
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import file_join
from file_join import classify_run_dir


REQUIRED_SOURCES = (
    "doom/session_map01_v12.py",
    "doom/session_map01_v13.py",
    "doom/map01_scorer_stdio_adapter_v1.py",
    "doom/main_thread_scorer_polling_v1.py",
    "doom/independent_progress_clock_v2.py",
    "doom/doom_retained_input_backend_v3.py",
    "live_control/input_transition_owner_v3.py",
)


def _json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


class RuntimeBundleJoinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.run_dir = self.root / "run"
        self.run_dir.mkdir()
        self.research = self.root / "research"
        self.research.mkdir()
        source_root = Path(__file__).resolve().parents[2]
        self.sources = {}
        for name in REQUIRED_SOURCES:
            path = self.research / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((source_root / name).read_bytes())
            self.sources[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        freeze = json.loads((Path(__file__).resolve().parent
                             / "FILE_JOIN_BUNDLE_A02_FREEZE.json").read_text(encoding="utf-8"))
        self.assertEqual(self.sources, freeze["required_source_sha256"])
        self._write_bundle()

    def tearDown(self):
        self.temp.cleanup()

    def _write_bundle(self):
        events = [
            {"event": "command", "received_ns": 99, "emit_ns": 99},
            {"event": "accepted", "id": "recover-1", "accepted_ns": 100,
             "emit_ns": 100},
            {"event": "input_admission", "id": "recover-1", "key": "space",
             "admitted_ns": 120, "input_ack_ns": 121, "emit_ns": 121},
        ]
        samples = [_sample(110, 0), _sample(130, 1)]
        score_events = [{"schema": "independent-progress-event-v2",
                         "event_sequence": 1, "observed_ns": 130,
                         "kind": "KILL_COUNT_INCREASE", "polarity": "positive",
                         "useful": True, "controller_visible": False,
                         "before": {"kill_count": 0},
                         "after": {"kill_count": 1, "delta": 1}}]
        _jsonl(self.run_dir / "events.jsonl", events)
        _jsonl(self.run_dir / "scorer-samples.jsonl", samples)
        _jsonl(self.run_dir / "scorer-events.jsonl", score_events)
        _json(self.run_dir / "sources.json", self.sources)
        _json(self.run_dir / "scorer-summary.json", {
            "schema": "map01-independent-scorer-integration-v3",
            "controller_visible": False,
            "sample_count": 2,
            "event_count": 1,
            "event_summary": {"events": 1, "positive_useful_events": 1,
                              "negative_events": 0, "first_useful_ns": 130,
                              "kinds": ["KILL_COUNT_INCREASE"]},
            "scheduler": {"missed_sample_periods": 0},
            "sample_interval_ms": {"median": 2e-05, "p95": 2e-05, "max": 2e-05},
            "zero_positive_events_allowed": True,
        })

    def _classify(self):
        return classify_run_dir(self.run_dir, "recover-1", max_gap_ns=100,
                                research_root=self.research)

    def _write_progress_rows(self, samples, score_events):
        _jsonl(self.run_dir / "scorer-samples.jsonl", samples)
        _jsonl(self.run_dir / "scorer-events.jsonl", score_events)
        times = [row["payload"]["sample_ns"] for row in samples]
        intervals = [b - a for a, b in zip(times, times[1:])]
        if intervals:
            ordered = sorted(intervals)
            interval_summary = {
                "median": statistics.median(intervals) / 1e6,
                "p95": ordered[min(len(ordered) - 1,
                                    round(.95 * (len(ordered) - 1)))] / 1e6,
                "max": max(intervals) / 1e6,
            }
        else:
            interval_summary = None
        useful = [row for row in score_events if row["useful"] is True]
        _json(self.run_dir / "scorer-summary.json", {
            "schema": "map01-independent-scorer-integration-v3",
            "controller_visible": False,
            "sample_count": len(samples),
            "event_count": len(score_events),
            "event_summary": {
                "events": len(score_events),
                "positive_useful_events": len(useful),
                "negative_events": sum(row["polarity"] == "negative"
                                        for row in score_events),
                "first_useful_ns": min((row["observed_ns"] for row in useful),
                                        default=None),
                "kinds": [row["kind"] for row in score_events],
            },
            "scheduler": {"missed_sample_periods": 0},
            "sample_interval_ms": interval_summary,
            "zero_positive_events_allowed": True,
        })

    def test_valid_single_directory_bundle_preserves_bounded_join(self):
        result = self._classify()
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertEqual(result["positive_sample_ns"], 130)
        self.assertIs(result["causal_attribution"], False)

    def test_cli_consumes_one_bundle_directory(self):
        output = io.StringIO()
        with patch("sys.argv", ["file_join.py", "--run-dir", str(self.run_dir),
                                 "--research-root", str(self.research),
                                 "--intent-id", "recover-1", "--max-gap-ns", "100"]):
            with redirect_stdout(output):
                file_join.main()
        self.assertEqual(json.loads(output.getvalue())["decision"],
                         "ADMISSION_BRACKETED_PROGRESS")

    def test_missing_sources_fails_closed(self):
        (self.run_dir / "sources.json").unlink()
        self._assert_invalid_bundle()

    def test_missing_required_source_fails_closed(self):
        del self.sources[REQUIRED_SOURCES[0]]
        _json(self.run_dir / "sources.json", self.sources)
        self._assert_invalid_bundle()

    def test_missing_summary_fails_closed(self):
        (self.run_dir / "scorer-summary.json").unlink()
        self._assert_invalid_bundle()

    def test_source_hash_mismatch_fails_closed(self):
        path = self.research / REQUIRED_SOURCES[0]
        path.write_text("changed source\n", encoding="utf-8")
        self._assert_invalid_bundle()

    def test_source_path_traversal_fails_closed(self):
        self.sources["../../outside.py"] = "0" * 64
        _json(self.run_dir / "sources.json", self.sources)
        self._assert_invalid_bundle()

    def test_summary_sample_count_mismatch_fails_closed(self):
        path = self.run_dir / "scorer-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["sample_count"] = 99
        _json(path, summary)
        self._assert_invalid_bundle()

    def test_summary_interval_mismatch_fails_closed(self):
        path = self.run_dir / "scorer-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["sample_interval_ms"]["max"] = 999
        _json(path, summary)
        self._assert_invalid_bundle()

    def test_summary_event_mismatch_fails_closed(self):
        path = self.run_dir / "scorer-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["event_summary"]["first_useful_ns"] = 110
        _json(path, summary)
        self._assert_invalid_bundle()

    def test_scorer_event_rejects_non_object_before_state(self):
        path = self.run_dir / "scorer-events.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["before"] = "not-an-object"
        _jsonl(path, rows)
        self._assert_invalid_bundle()

    def test_kill_event_rejects_impossible_counter_delta(self):
        path = self.run_dir / "scorer-events.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["before"] = {"kill_count": 1}
        rows[0]["after"] = {"kill_count": 0, "delta": -1}
        _jsonl(path, rows)
        self._assert_invalid_bundle()

    def test_progress_event_kinds_match_adjacent_samples(self):
        samples = [_sample(110, 0), _sample(130, 1), _sample(140, 1),
                   _sample(150, 1)]
        samples[1]["payload"]["death_count"] = 1
        samples[2]["payload"].update({"death_count": 1, "episode_finished": True,
                                      "player_dead": True})
        samples[3]["payload"].update({"death_count": 1, "episode_finished": True,
                                      "player_dead": True})
        score_events = [
            {"schema": "independent-progress-event-v2", "event_sequence": 1,
             "observed_ns": 130, "kind": "KILL_COUNT_INCREASE",
             "polarity": "positive", "useful": True, "controller_visible": False,
             "before": {"kill_count": 0}, "after": {"kill_count": 1, "delta": 1}},
            {"schema": "independent-progress-event-v2", "event_sequence": 2,
             "observed_ns": 130, "kind": "DEATH_COUNT_INCREASE",
             "polarity": "negative", "useful": False, "controller_visible": False,
             "before": {"death_count": 0}, "after": {"death_count": 1, "delta": 1}},
            {"schema": "independent-progress-event-v2", "event_sequence": 3,
             "observed_ns": 140, "kind": "PLAYER_DEAD",
             "polarity": "negative", "useful": False, "controller_visible": False,
             "before": {"player_dead": False}, "after": {"player_dead": True}},
            {"schema": "independent-progress-event-v2", "event_sequence": 4,
             "observed_ns": 140, "kind": "EPISODE_FINISHED_NO_EXIT",
             "polarity": "negative", "useful": False, "controller_visible": False,
             "before": {"episode_finished": False},
             "after": {"episode_finished": True, "player_dead": True,
                       "map_exit": False}},
        ]
        self._write_progress_rows(samples, score_events)
        result = self._classify()
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS", result)
        self.assertIs(result["causal_attribution"], False)

    def test_map_exit_event_matches_adjacent_samples(self):
        samples = [_sample(110, 0), _sample(130, 0)]
        samples[1]["payload"].update({"episode_finished": True, "map_exit": True})
        score_events = [{
            "schema": "independent-progress-event-v2", "event_sequence": 1,
            "observed_ns": 130, "kind": "MAP_EXIT", "polarity": "positive",
            "useful": True, "controller_visible": False,
            "before": {"map_exit": False, "episode_finished": False},
            "after": {"map_exit": True, "episode_finished": True},
        }]
        self._write_progress_rows(samples, score_events)
        result = self._classify()
        self.assertEqual(result["decision"], "ADMISSION_BRACKETED_PROGRESS")
        self.assertIs(result["causal_attribution"], False)

    def test_missing_scorer_events_fails_closed(self):
        (self.run_dir / "scorer-events.jsonl").unlink()
        self._assert_invalid_bundle()

    def _assert_invalid_bundle(self):
        result = self._classify()
        self.assertEqual(result["decision"], "POST_CANCELLATION_COOCCURRENCE")
        self.assertEqual(result["reason"], "invalid_or_missing_run_bundle")
        self.assertIs(result["causal_attribution"], False)


if __name__ == "__main__":
    unittest.main()
