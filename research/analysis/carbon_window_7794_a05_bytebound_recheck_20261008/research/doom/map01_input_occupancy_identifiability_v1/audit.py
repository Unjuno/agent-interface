"""Independent raw-only audit; deliberately does not import analyze.py."""

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RELATIVE = Path("research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl")
EXPECTED_SHA256 = "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381"
EXPECTED_COUNTS = {
    "accepted": 9,
    "cancel_requested": 7,
    "clock_probe": 1,
    "coast_result": 8,
    "command": 17,
    "input_admission": 39,
    "input_released": 1,
    "keys_held": 28,
    "observation": 218,
    "post_control_score": 1,
    "ready": 1,
    "step_completed": 35,
    "step_started": 42,
    "terminal": 9,
    "typed_observation": 218,
}


def main():
    raw = (ROOT / RELATIVE).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == EXPECTED_SHA256, (digest, EXPECTED_SHA256)
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    counts = Counter(row.get("event", "<missing>") for row in rows)
    assert len(rows) == 634, len(rows)
    assert dict(sorted(counts.items())) == EXPECTED_COUNTS, counts

    terminals = [row for row in rows if row.get("event") == "terminal"]
    assert all(
        row.get("release", {}).get("verified") is True
        and row["release"].get("keys_down") == []
        and row["release"].get("buttons_down") == []
        and isinstance(row["release"].get("verified_ns"), int)
        for row in terminals
    )
    releases = [row for row in rows if row.get("event") == "input_released"]
    assert len(releases) == 1
    release = releases[0].get("owner_release", {})
    assert (
        release.get("verified") is True
        and release.get("keys_down") == []
        and release.get("buttons_down") == []
        and isinstance(release.get("verified_ns"), int)
    )
    per_key_release = [
        row
        for row in rows
        if row.get("event") in {"key_up", "key_released", "input_key_released"}
        and (row.get("key") or row.get("key_name"))
        and any(
            isinstance(row.get(field), int)
            for field in ("release_ns", "released_ns", "verified_ns", "timestamp_ns")
        )
    ]
    assert not per_key_release, per_key_release

    print(json.dumps({
        "audit": "PASS_RAW_IDENTIFIABILITY_LIMIT",
        "raw_sha256": digest,
        "rows": len(rows),
        "event_counts": dict(sorted(counts.items())),
        "verified_empty_terminals": len(terminals),
        "verified_empty_input_released": len(releases),
        "per_key_release_timestamps": len(per_key_release),
        "occupancy_duration_identifiable": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
