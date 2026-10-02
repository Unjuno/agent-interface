#!/usr/bin/env python3
"""One-shot selector run; outcome labels are not loaded by this process."""
import argparse
import hashlib
import json
from pathlib import Path

from runner import rank_optional

POLICIES = (
    "DUAL", "NOVELTY_ONLY", "EFFECT_ONLY", "5435_SEVERITY_ONLY",
    "5435_SAFE_IDENTITY_BATCH", "CHRONOLOGICAL",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_raw(stream_path):
    stream_path = Path(stream_path)
    stream = json.loads(stream_path.read_text(encoding="utf-8"))
    events = stream["events"]
    if len({row["event_id"] for row in events}) != len(events):
        raise ValueError("event IDs must be unique")
    budget = stream["optional_audit_budget"]
    decisions = {}
    for policy in POLICIES:
        decisions[policy] = rank_optional(events, policy, budget)
    return {
        "schema": "issue-5764-triage-selection-v1",
        "stream_sha256": digest(stream_path),
        "population_size": len(events),
        "mandatory_event_ids": sorted(row["event_id"] for row in events if row["mandatory"]),
        "optional_audit_budget": budget,
        "decisions": decisions,
        "scope": "synthetic pre-audit selection only; no outcomes scored",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", default="preaudit_stream.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raw = json.dumps(build_raw(args.stream), sort_keys=True, indent=2) + "\n"
    Path(args.output).write_text(raw, encoding="utf-8")
    print(raw, end="")


if __name__ == "__main__":
    main()
