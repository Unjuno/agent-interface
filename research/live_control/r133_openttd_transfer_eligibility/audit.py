#!/usr/bin/env python3
"""Read-only, source-pinned audit of retained OpenTTD input/effect evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

EXPECTED = {
    "events_sha256": "b9e707b006a918b232f6d8915adc6a95e4d7e4ee789fec7ef4e1fba7e2df61ae",
    "observer_sha256": "4bcfb5b2632e9b2dc76f5e3f67a73f30cbd6b142578b495f0b204a2ec9696ca4",
    "posthoc_sha256": "8377e663d6f3b88eb41b73d85212f903f21b4879010835f9e2d1f100de4bee5c",
}
EVENT_COUNTS = {
    "ready": 1, "observation": 52, "command": 50, "clock": 25,
    "accepted": 25, "step_started": 51, "input_admission": 2,
    "step_completed": 51, "terminal": 25, "pointer_admission": 29,
}
TARGET = (977, 978, 979)
SECOND_LEG = (1043, 1107)
FORBIDDEN = (1041, 1042, 1105, 1106)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_observer(raw: bytes) -> list[dict]:
    rows = []
    for line in raw.decode("utf-8").splitlines():
        marker = "AIT "
        if marker in line:
            rows.append(json.loads(line.split(marker, 1)[1]))
    return rows


def effect_state(row: dict) -> tuple:
    tiles = {int(t["id"]): (bool(t["road"]), int(t["owner"])) for t in row["tiles"]}
    ids = TARGET + SECOND_LEG + FORBIDDEN
    return tuple((tile, *tiles[tile]) for tile in ids)


def analyze(event_rows: list[dict], observer_rows: list[dict], posthoc: dict) -> dict:
    counts = Counter(row.get("event") for row in event_rows)
    if dict(counts) != EVENT_COUNTS:
        raise ValueError("event ledger row/count mismatch")

    pointer = [r for r in event_rows if r.get("event") == "pointer_admission"]
    downs = [r for r in pointer if r.get("operation") == "button_down"]
    ups = [r for r in pointer if r.get("operation") == "button_up"]
    if len(downs) != 7 or len(ups) != 0:
        raise ValueError("button-down/up event coverage mismatch")
    terminals = {r.get("id"): r for r in event_rows if r.get("event") == "terminal"}
    joined = []
    for down in downs:
        ident = down.get("id")
        end = terminals.get(ident)
        if not ident or not isinstance(down.get("input_ack_ns"), int) or not end:
            raise ValueError("button-down lacks identity, input acknowledgment, or terminal")
        release = end.get("release") or {}
        if release.get("verified") is not True:
            raise ValueError("matching terminal lacks verified release")
        if release.get("buttons_down") != [] or release.get("keys_down") != []:
            raise ValueError("matching release is not neutral")
        verified_ns = release.get("verified_ns")
        if not isinstance(verified_ns, int) or verified_ns < down["input_ack_ns"]:
            raise ValueError("release timestamp missing or precedes acknowledgment")
        joined.append({
            "id": ident, "step": down.get("step"),
            "input_ack_ns": down["input_ack_ns"],
            "neutral_verified_ns": verified_ns,
            "ack_to_neutral_confirmation_ns": verified_ns - down["input_ack_ns"],
        })

    if len(observer_rows) != 263:
        raise ValueError("independent observer record-count mismatch")
    states = [effect_state(r) for r in observer_rows]
    unique = set(states)
    first_target = next(
        (i for i, r in enumerate(observer_rows)
         if all(any(int(t["id"]) == tile and t["road"] is True and t["owner"] == 0
                    for t in r["tiles"]) for tile in TARGET)),
        None,
    )
    if len(unique) != 2 or first_target != 91:
        raise ValueError("observer state/transition mismatch")
    if any(any(any(int(t["id"]) == tile and t["road"] for t in r["tiles"])
                   for tile in FORBIDDEN) for r in observer_rows):
        raise ValueError("forbidden road appeared in independent observer")
    if any(any(any(int(t["id"]) == tile and t["road"] for t in r["tiles"])
                   for tile in SECOND_LEG) for r in observer_rows[-1:]):
        raise ValueError("second-leg state disagrees with retained posthoc")

    observer_keys = set().union(*(r.keys() for r in observer_rows))
    host_observations = [r for r in event_rows if r.get("event") == "observation"]
    host_keys = set().union(*(r.keys() for r in host_observations))
    clock_or_join_fields = {
        "sequence", "capture_ns", "timestamp_ns", "monotonic_ns", "id"
    }
    shared_fields = observer_keys & host_keys
    shared_join_fields = shared_fields & clock_or_join_fields
    if shared_join_fields:
        raise ValueError("unexpected observer/host clock or identity join field")
    if any(re.search(r"(?:mono|timestamp|capture_ns|sequence)", k, re.I)
           for k in observer_keys):
        raise ValueError("observer unexpectedly contains a host-clock/sequence field")

    retained = posthoc["continuous_independent_observer_outcome"]
    if (retained["records"] != len(observer_rows)
            or retained["transition_indices"] != [91]
            or retained["status"] != "partial_A_to_B_only"
            or posthoc["hard_success"] is not False):
        raise ValueError("posthoc summary does not match raw observer")

    return {
        "classification": "HOLD_CROSS_DOMAIN_EFFECT_CLOCK_JOIN",
        "event_rows": len(event_rows),
        "event_counts": dict(counts),
        "pointer_admissions": len(pointer),
        "button_down_admissions": len(downs),
        "button_up_admissions": len(ups),
        "unique_button_down_programs": len({r["id"] for r in downs}),
        "down_to_neutral_receipts": joined,
        "observer_records": len(observer_rows),
        "observer_unique_declared_states": len(unique),
        "first_A_to_B_observer_record_zero_based": first_target,
        "observer_top_level_keys": sorted(observer_keys),
        "host_observation_rows": len(host_observations),
        "host_observation_sequence_range": [
            min(r["sequence"] for r in host_observations),
            max(r["sequence"] for r in host_observations),
        ],
        "shared_observer_host_clock_or_identity_fields": sorted(shared_join_fields),
        "exact_per_button_hold_duration": "NOT_IDENTIFIABLE",
        "observer_effect_latency_on_host_clock": "NOT_IDENTIFIABLE",
        "interpretation": (
            "The same-program terminal confirms a later neutral input state, but "
            "input_ack_ns-to-neutral_verified_ns is only a request/confirmation "
            "interval, not button occupancy. The independently observed A-to-B "
            "transition has no shared host monotonic timestamp, sequence, or ID, "
            "so effect latency cannot be joined."
        ),
        "scope": "one immutable archived OpenTTD episode; no new model, GUI, input, game, or live claim",
    }


def run(events_path: Path, observer_path: Path, posthoc_path: Path, output_path: Path) -> dict:
    raw_events = events_path.read_bytes()
    raw_observer = observer_path.read_bytes()
    raw_posthoc = posthoc_path.read_bytes()
    hashes = {
        "events_sha256": sha256(raw_events),
        "observer_sha256": sha256(raw_observer),
        "posthoc_sha256": sha256(raw_posthoc),
    }
    if hashes != EXPECTED:
        raise ValueError(f"source hash mismatch: {hashes}")
    event_rows = [json.loads(line) for line in raw_events.decode("utf-8").splitlines() if line]
    result = analyze(event_rows, read_observer(raw_observer), json.loads(raw_posthoc))
    result["source_sha256"] = hashes
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--observer-log", type=Path, required=True)
    parser.add_argument("--posthoc", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.events, args.observer_log, args.posthoc, args.output),
                     sort_keys=True))


if __name__ == "__main__":
    main()

