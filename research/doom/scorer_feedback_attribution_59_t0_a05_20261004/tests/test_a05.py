from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENTS = ROOT / "parents"
sys.path.insert(0, str(PARENTS / "scorer_feedback_attribution_59_t0_a04_20261004"))
sys.path.insert(0, str(PARENTS / "main"))

from scorer_feedback_attribution_v4 import (  # noqa: E402
    POSITIVE_USEFUL_EVENT_KINDS,
    attribute_positive_events,
)
from independent_progress_clock_v2 import ProgressClock, ProgressSample  # noqa: E402


def envelope(samples, event):
    return attribute_positive_events(
        samples,
        [event],
        [{"intent_token": "intent-a", "key": "ATTACK", "admitted_ns": 90,
          "release_sync_ns": 210, "release_verified": True}],
    )


def clock_events(after: ProgressSample):
    clock = ProgressClock()
    clock.ingest(ProgressSample(100, 0, 0, False, False, False))
    return clock.ingest(after)


def test_actual_producer_positive_vocabulary_is_frozen_to_two_kinds():
    kill_events = clock_events(ProgressSample(200, 1, 0, False, False, False))
    exit_events = clock_events(ProgressSample(200, 0, 0, True, False, True))
    generated = {row["kind"] for row in kill_events + exit_events
                 if row["polarity"] == "positive" and row["useful"] is True}
    assert generated == POSITIVE_USEFUL_EVENT_KINDS
    for event in kill_events + exit_events:
        if event["polarity"] == "positive" and event["useful"] is True:
            rows = envelope([{"schema":"independent-progress-sample-v2","sample_ns":100},
                             {"schema":"independent-progress-sample-v2","sample_ns":200}], event)
            assert rows[0]["status"] == "SINGLE_POSSIBLE_INTENT_ENVELOPE"
            assert rows[0]["intent_token"] is None
            assert rows[0]["causal_attribution"] == "NOT_ESTABLISHED"


def test_unknown_nonempty_positive_kind_is_rejected():
    event = {"schema":"independent-progress-event-v2","event_sequence":1,"observed_ns":200,
             "kind":"FUTURE_SCORER_EVENT_V3","polarity":"positive","useful":True,
             "controller_visible":False}
    try:
        envelope([{"schema":"independent-progress-sample-v2","sample_ns":100},
                  {"schema":"independent-progress-sample-v2","sample_ns":200}], event)
    except ValueError as error:
        assert "outside v2 producer vocabulary" in str(error)
    else:
        raise AssertionError("unknown positive kind was accepted")


def test_misspelled_known_kind_is_rejected():
    event = {"schema":"independent-progress-event-v2","event_sequence":1,"observed_ns":200,
             "kind":"KILL_COUNT_INCREASEE","polarity":"positive","useful":True,
             "controller_visible":False}
    try:
        envelope([{"schema":"independent-progress-sample-v2","sample_ns":100},
                  {"schema":"independent-progress-sample-v2","sample_ns":200}], event)
    except ValueError:
        pass
    else:
        raise AssertionError("misspelled positive kind was accepted")


def test_producer_defined_negative_event_stays_excluded():
    negative = clock_events(ProgressSample(200, 0, 1, True, True, False))
    assert {row["kind"] for row in negative} == {"DEATH_COUNT_INCREASE", "PLAYER_DEAD", "EPISODE_FINISHED_NO_EXIT"}
    samples = [{"schema":"independent-progress-sample-v2","sample_ns":100},
               {"schema":"independent-progress-sample-v2","sample_ns":200}]
    for event in negative:
        assert envelope(samples, event) == []


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_"):
            function()
            print(f"PASS {name}")
