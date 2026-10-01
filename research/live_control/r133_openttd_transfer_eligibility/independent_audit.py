#!/usr/bin/env python3
"""Independent raw-only checker; intentionally does not import audit.py."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

PINNED = {
    "events_sha256": "b9e707b006a918b232f6d8915adc6a95e4d7e4ee789fec7ef4e1fba7e2df61ae",
    "observer_sha256": "4bcfb5b2632e9b2dc76f5e3f67a73f30cbd6b142578b495f0b204a2ec9696ca4",
    "posthoc_sha256": "8377e663d6f3b88eb41b73d85212f903f21b4879010835f9e2d1f100de4bee5c",
}
EXPECTED_COUNTS = {
    "ready": 1, "observation": 52, "command": 50, "clock": 25,
    "accepted": 25, "step_started": 51, "input_admission": 2,
    "step_completed": 51, "terminal": 25, "pointer_admission": 29,
}
TARGET = {977, 978, 979}
SECOND = {1043, 1107}
FORBIDDEN = {1041, 1042, 1105, 1106}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_observer(data: bytes) -> list[dict]:
    result = []
    for line in data.decode("utf-8").splitlines():
        pos = line.find("AIT ")
        if pos >= 0:
            result.append(json.loads(line[pos + 4:]))
    return result


def check(events_file: Path, observer_file: Path, posthoc_file: Path,
          candidate_file: Path, output_file: Path) -> dict:
    event_bytes, observer_bytes, posthoc_bytes = (
        events_file.read_bytes(), observer_file.read_bytes(), posthoc_file.read_bytes()
    )
    seen = {
        "events_sha256": digest(event_bytes),
        "observer_sha256": digest(observer_bytes),
        "posthoc_sha256": digest(posthoc_bytes),
    }
    if seen != PINNED:
        raise ValueError("raw input hash mismatch")
    rows = [json.loads(line) for line in event_bytes.decode("utf-8").splitlines() if line]
    counts = Counter(row.get("event") for row in rows)
    if dict(counts) != EXPECTED_COUNTS:
        raise ValueError("independent event counts mismatch")

    down = [r for r in rows if r.get("event") == "pointer_admission"
            and r.get("operation") == "button_down"]
    up = [r for r in rows if r.get("event") == "pointer_admission"
          and r.get("operation") == "button_up"]
    end_by_id = {r.get("id"): r for r in rows if r.get("event") == "terminal"}
    intervals = []
    for start in down:
        end = end_by_id.get(start.get("id"))
        if not end or not isinstance(start.get("input_ack_ns"), int):
            raise ValueError("independent down/terminal identity join failed")
        receipt = end.get("release") or {}
        t = receipt.get("verified_ns")
        if (receipt.get("verified") is not True or receipt.get("buttons_down") != []
                or receipt.get("keys_down") != [] or not isinstance(t, int)
                or t < start["input_ack_ns"]):
            raise ValueError("independent neutral-release witness failed")
        intervals.append(t - start["input_ack_ns"])

    observer = parse_observer(observer_bytes)
    if len(observer) != 263:
        raise ValueError("independent observer row count mismatch")
    states = {
        tuple((int(t["id"]), bool(t["road"]), int(t["owner"]))
              for t in row["tiles"] if int(t["id"]) in TARGET | SECOND | FORBIDDEN)
        for row in observer
    }
    first = next((i for i, row in enumerate(observer)
                  if all(any(int(t["id"]) == tile and t["road"] is True and t["owner"] == 0
                             for t in row["tiles"]) for tile in TARGET)), None)
    if len(states) != 2 or first != 91:
        raise ValueError("independent effect transition reconstruction failed")
    if any(t["road"] for row in observer for t in row["tiles"]
           if int(t["id"]) in FORBIDDEN):
        raise ValueError("forbidden tile is not clear")
    if any(t["road"] for row in observer[-1:] for t in row["tiles"]
           if int(t["id"]) in SECOND):
        raise ValueError("second-leg outcome differs from independent observer")

    observer_fields = {key for row in observer for key in row}
    obs_rows = [r for r in rows if r.get("event") == "observation"]
    host_fields = {key for row in obs_rows for key in row}
    shared_clock_or_ids = sorted(
        (observer_fields & host_fields) & {"sequence", "capture_ns", "timestamp_ns",
                                            "monotonic_ns", "id"}
    )
    if shared_clock_or_ids:
        raise ValueError("unexpected observer/host join key")
    posthoc = json.loads(posthoc_bytes)
    stated = posthoc["continuous_independent_observer_outcome"]
    if (stated["records"] != 263 or stated["transition_indices"] != [91]
            or stated["status"] != "partial_A_to_B_only" or posthoc["hard_success"]):
        raise ValueError("retained posthoc contract disagrees with raw observer")

    candidate = json.loads(candidate_file.read_text(encoding="utf-8"))
    if (candidate.get("classification") != "HOLD_CROSS_DOMAIN_EFFECT_CLOCK_JOIN"
            or candidate.get("button_down_admissions") != len(down)
            or candidate.get("button_up_admissions") != len(up)
            or candidate.get("observer_records") != len(observer)
            or candidate.get("first_A_to_B_observer_record_zero_based") != first
            or candidate.get("exact_per_button_hold_duration") != "NOT_IDENTIFIABLE"
            or candidate.get("observer_effect_latency_on_host_clock") != "NOT_IDENTIFIABLE"
            or candidate.get("source_sha256") != seen
            or len(candidate.get("down_to_neutral_receipts", [])) != len(down)):
        raise ValueError("candidate output differs from independent reconstruction")

    result = {
        "status": "PASS_RAW_AUDIT_OF_HOLD_CLASSIFICATION",
        "source_sha256": seen,
        "reconstructed": {
            "event_rows": len(rows), "button_down_admissions": len(down),
            "button_up_admissions": len(up),
            "down_to_neutral_receipts": len(intervals),
            "ack_to_neutral_confirmation_ns_min": min(intervals),
            "ack_to_neutral_confirmation_ns_max": max(intervals),
            "observer_records": len(observer), "unique_observer_states": len(states),
            "first_A_to_B_record_zero_based": first,
            "shared_clock_or_identity_fields": shared_clock_or_ids,
        },
        "scope": "raw reconstruction only; the HOLD is supported, not converted into an occupancy/effect latency estimate",
    }
    output_file.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--events", type=Path, required=True)
    p.add_argument("--observer-log", type=Path, required=True)
    p.add_argument("--posthoc", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(check(a.events, a.observer_log, a.posthoc, a.candidate, a.output),
                     sort_keys=True))


if __name__ == "__main__":
    main()

