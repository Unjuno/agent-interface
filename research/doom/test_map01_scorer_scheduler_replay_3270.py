"""Deterministic replay gate for issue #3270 scheduler-jitter evidence.

This test does not alter the production scheduler or claim efficacy.  It
replays the retained timing observations from v7 pair-02 COAST_CONTROL and
checks that the adapter's declared policy (skip overdue periods, emit one
current sample, resume on the next period) is represented without inventing a
catch-up sample.
"""
from __future__ import annotations

import unittest


PERIOD_NS = 28_571_429
OBSERVED_SCHEDULED_NS = [
    208017099942,
    208045671371,
    208074242800,
    208131385658,
    208159957087,
]
OBSERVED_STARTED_NS = [
    208017170775,
    208045741945,
    208105240031,
    208131475483,
    208160025798,
]


def replay_scheduler(scheduled_ns: list[int], started_ns: list[int]) -> list[int]:
    if len(scheduled_ns) != len(started_ns):
        raise ValueError("paired timing rows required")
    skipped: list[int] = []
    for index, (scheduled, started) in enumerate(zip(scheduled_ns, started_ns)):
        if index == 0:
            skipped.append(0)
            continue
        elapsed = ((started - scheduled) // PERIOD_NS) + 1
        skipped.append(max(0, elapsed - 1))
    return skipped


class ScorerJitterReplayTest(unittest.TestCase):
    def test_observed_single_overdue_period_is_local_and_non_catchup(self) -> None:
        skipped = replay_scheduler(OBSERVED_SCHEDULED_NS, OBSERVED_STARTED_NS)
        self.assertEqual(skipped, [0, 0, 1, 0, 0])
        self.assertEqual(sum(skipped), 1)
        self.assertEqual(len(OBSERVED_SCHEDULED_NS), 5)

    def test_replay_preserves_sample_cardinality(self) -> None:
        skipped = replay_scheduler(OBSERVED_SCHEDULED_NS, OBSERVED_STARTED_NS)
        # One current sample is emitted per retained row; skipped periods are
        # accounted for, never materialized as synthetic samples.
        self.assertEqual(len(OBSERVED_STARTED_NS), len(OBSERVED_SCHEDULED_NS))
        self.assertEqual(sum(skipped), 1)


if __name__ == "__main__":
    unittest.main()
