"""Scorer-only progress event clock for MAP01-style independent evaluation.

This module is deliberately detached from controller/runtime delivery. It turns
successive *independent scorer* samples into append-only, timestamped outcome
events. It does not read screenshots, health/ammo HUD values, controller events,
or input authority, and it has no method that sends data to a controller.

Integration is intentionally deferred. A future adapter may persist these events
to a scorer-only JSONL stream after proving that privileged engine state never
enters the controller-visible channel.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable


EVENT_SCHEMA = "independent-progress-event-v1"
SAMPLE_SCHEMA = "independent-progress-sample-v1"


@dataclass(frozen=True)
class ProgressSample:
    """One independently sampled task-outcome state."""

    sample_ns: int
    kill_count: int
    death_count: int
    episode_finished: bool
    player_dead: bool
    map_exit: bool

    def validate(self) -> None:
        if type(self.sample_ns) is not int or self.sample_ns < 0:
            raise ValueError("sample_ns must be a non-negative integer")
        if type(self.kill_count) is not int or self.kill_count < 0:
            raise ValueError("kill_count must be a non-negative integer")
        if type(self.death_count) is not int or self.death_count < 0:
            raise ValueError("death_count must be a non-negative integer")
        for name in ("episode_finished", "player_dead", "map_exit"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be bool")
        if self.map_exit and (not self.episode_finished or self.player_dead):
            raise ValueError("map_exit requires episode_finished and alive player")

    def as_dict(self) -> dict:
        return {
            "schema": SAMPLE_SCHEMA,
            "sample_ns": self.sample_ns,
            "kill_count": self.kill_count,
            "death_count": self.death_count,
            "episode_finished": self.episode_finished,
            "player_dead": self.player_dead,
            "map_exit": self.map_exit,
        }


class ProgressClock:
    """Convert monotonic scorer samples into typed positive/negative events.

    The first sample establishes the episode baseline and emits no event. Exact
    duplicate samples at the same timestamp are idempotent. A same-timestamp
    mutation, timestamp regression, counter regression, or impossible map-exit
    state fails closed rather than inventing an ordering/episode transition.
    """

    def __init__(self) -> None:
        self._last: ProgressSample | None = None
        self._event_sequence = 0

    @property
    def last_sample(self) -> ProgressSample | None:
        return self._last

    def _event(
        self,
        *,
        observed_ns: int,
        kind: str,
        polarity: str,
        useful: bool,
        before: dict,
        after: dict,
    ) -> dict:
        self._event_sequence += 1
        return {
            "schema": EVENT_SCHEMA,
            "event_sequence": self._event_sequence,
            "observed_ns": observed_ns,
            "kind": kind,
            "polarity": polarity,
            "useful": useful,
            "controller_visible": False,
            "before": before,
            "after": after,
        }

    def ingest(self, sample: ProgressSample) -> list[dict]:
        sample.validate()
        previous = self._last
        if previous is None:
            self._last = sample
            return []

        if sample.sample_ns < previous.sample_ns:
            raise ValueError("scorer timestamp regression")
        if sample.sample_ns == previous.sample_ns:
            if sample == previous:
                return []
            raise ValueError("state changed without a later scorer timestamp")
        if sample.kill_count < previous.kill_count:
            raise ValueError("kill_count regression requires a new scorer epoch")
        if sample.death_count < previous.death_count:
            raise ValueError("death_count regression requires a new scorer epoch")
        if previous.episode_finished and not sample.episode_finished:
            raise ValueError("episode_finished regression requires a new scorer epoch")
        if previous.map_exit and not sample.map_exit:
            raise ValueError("map_exit regression requires a new scorer epoch")

        events: list[dict] = []

        if sample.kill_count > previous.kill_count:
            events.append(self._event(
                observed_ns=sample.sample_ns,
                kind="KILL_COUNT_INCREASE",
                polarity="positive",
                useful=True,
                before={"kill_count": previous.kill_count},
                after={
                    "kill_count": sample.kill_count,
                    "delta": sample.kill_count - previous.kill_count,
                },
            ))

        if sample.death_count > previous.death_count:
            events.append(self._event(
                observed_ns=sample.sample_ns,
                kind="DEATH_COUNT_INCREASE",
                polarity="negative",
                useful=False,
                before={"death_count": previous.death_count},
                after={
                    "death_count": sample.death_count,
                    "delta": sample.death_count - previous.death_count,
                },
            ))

        if sample.player_dead and not previous.player_dead:
            events.append(self._event(
                observed_ns=sample.sample_ns,
                kind="PLAYER_DEAD",
                polarity="negative",
                useful=False,
                before={"player_dead": False},
                after={"player_dead": True},
            ))

        if sample.map_exit and not previous.map_exit:
            events.append(self._event(
                observed_ns=sample.sample_ns,
                kind="MAP_EXIT",
                polarity="positive",
                useful=True,
                before={
                    "map_exit": previous.map_exit,
                    "episode_finished": previous.episode_finished,
                },
                after={"map_exit": True, "episode_finished": True},
            ))
        elif sample.episode_finished and not previous.episode_finished:
            events.append(self._event(
                observed_ns=sample.sample_ns,
                kind="EPISODE_FINISHED_NO_EXIT",
                polarity="negative",
                useful=False,
                before={"episode_finished": False},
                after={
                    "episode_finished": True,
                    "player_dead": sample.player_dead,
                    "map_exit": False,
                },
            ))

        self._last = sample
        return events


def summarize_events(events: Iterable[dict]) -> dict:
    rows = list(events)
    positive = [row for row in rows if row.get("useful") is True]
    negative = [row for row in rows if row.get("polarity") == "negative"]
    return {
        "events": len(rows),
        "positive_useful_events": len(positive),
        "negative_events": len(negative),
        "first_useful_ns": min((row["observed_ns"] for row in positive), default=None),
        "kinds": [row.get("kind") for row in rows],
    }


def append_jsonl(path: Path, events: Iterable[dict]) -> int:
    """Append scorer events to a scorer-owned JSONL file only."""
    rows = list(events)
    if not rows:
        return 0
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            if row.get("schema") != EVENT_SCHEMA:
                raise ValueError("unexpected scorer event schema")
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    return len(rows)
