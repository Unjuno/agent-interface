"""Replay the stale-submit rejection against the unmodified PR #7904 helper."""
import json
import os
from pathlib import Path
import queue
import sys
import types


PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]
SOURCE = PACKAGE / "baseline_controller.py"
os.environ["V39_WAIT_SOURCE"] = str(SOURCE)
sys.path.insert(0, str(ROOT / "research/doom"))
import test_overlap_controller_v39_wait as harness


class RecordingQueue:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.seen = []

    def get(self, timeout):
        row = next(self.rows, harness.EMPTY)
        if row is harness.EMPTY:
            raise queue.Empty()
        self.seen.append(row.get("event"))
        return row


observation = {"event": "observation", "sequence": 8, "health": 70}
rejected = {"event": "rejected",
            "reason": "latest observation sequence required before input"}
cancel_ack = {"event": "cancel_requested", "id": "cover-0", "matched": False}
events = RecordingQueue([observation, rejected, cancel_ack])
harness.ScriptQueue = lambda _rows: events
monitor = types.SimpleNamespace(
    event_types={"observation"},
    observe=lambda row: {"reason": "health_below_floor"} if row is observation else None)
process = types.SimpleNamespace(stdin=__import__("io").StringIO())
wait, latest = harness.extract_wait(harness.Process(None),
                                   [observation, rejected, cancel_ack])
submit = harness.extract_submit_cover(
    process, wait, {"sequence": 7}, [{"op": "hold"}], monitor, [])
submission = submit("cover-0")
cancel = harness.extract_top_level_function("cancel_invalidated_cover_before_plan")
try:
    cancel(process, wait, "cover-0")
except TimeoutError:
    disposition = "BASELINE_REPRODUCED_RELEASE_TIMEOUT"
else:
    raise SystemExit("baseline did not reproduce the missing-release wait")

result = {
    "disposition": disposition,
    "submission_event": submission.get("event"),
    "consumed_events": events.seen,
    "submitted_commands": [json.loads(line) for line in process.stdin.getvalue().splitlines()],
    "release_event_available": False,
    "timeout_is_expected_baseline_failure": True,
}
print(json.dumps(result, sort_keys=True))
