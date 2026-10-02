"""Test whether retained MAP01 events identify per-key physical occupancy."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def _has_explicit_key_release(row: dict[str, Any]) -> bool:
    """A per-key release needs a key identity and a release-time field."""
    event = str(row.get("event", "")).lower()
    if event not in {"key_up", "key_released", "input_key_released"}:
        return False
    has_key = bool(row.get("key") or row.get("key_name"))
    has_time = any(
        isinstance(row.get(name), int)
        for name in ("release_ns", "released_ns", "verified_ns", "timestamp_ns")
    )
    return has_key and has_time


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row.get("event", "<missing>") for row in rows)
    admissions = [row for row in rows if row.get("event") == "input_admission"]
    held = [row for row in rows if row.get("event") == "keys_held"]
    terminals = [row for row in rows if row.get("event") == "terminal"]
    input_released = [row for row in rows if row.get("event") == "input_released"]

    verified_empty_terminals = [
        row
        for row in terminals
        if isinstance(row.get("release"), dict)
        and row["release"].get("verified") is True
        and row["release"].get("keys_down") == []
        and row["release"].get("buttons_down") == []
        and isinstance(row["release"].get("verified_ns"), int)
    ]
    verified_empty_input_released = [
        row
        for row in input_released
        if isinstance(row.get("owner_release"), dict)
        and row["owner_release"].get("verified") is True
        and row["owner_release"].get("keys_down") == []
        and row["owner_release"].get("buttons_down") == []
        and isinstance(row["owner_release"].get("verified_ns"), int)
    ]

    return {
        "row_count": len(rows),
        "event_counts": dict(sorted(counts.items())),
        "input_admission_count": len(admissions),
        "distinct_admitted_keys": sorted(
            {row["key"] for row in admissions if isinstance(row.get("key"), str)}
        ),
        "keys_held_snapshot_count": len(held),
        "explicit_per_key_release_count": sum(
            _has_explicit_key_release(row) for row in rows
        ),
        "terminal_count": len(terminals),
        "verified_empty_terminal_count": len(verified_empty_terminals),
        "input_released_count": len(input_released),
        "verified_empty_input_released_count": len(verified_empty_input_released),
        "physical_occupancy_identifiable": any(
            _has_explicit_key_release(row) for row in rows
        ),
    }


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    source = root / "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"
    result = summarize(load_jsonl(source))
    result["source"] = "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"
    result["disposition"] = "PASS_IDENTIFIABILITY_LIMIT"
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
