"""Finite estimator for additional fresh exchanges given a current transcript."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def _validate(case: dict) -> tuple[list[dict], list[dict]]:
    worlds = case.get("worlds")
    if not isinstance(worlds, list) or len(worlds) < 2:
        raise ValueError("case requires at least two worlds")
    ids = [world.get("id") for world in worlds]
    if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("world ids must be unique non-empty strings")
    for world in worlds:
        actions = world.get("safe_progress_actions")
        if not isinstance(actions, list) or any(not isinstance(action, str) or not action for action in actions):
            raise ValueError("safe_progress_actions must be a string list")
    initial = case.get("initial_transcript")
    future = case.get("channels")
    if not isinstance(initial, list) or not isinstance(future, list):
        raise ValueError("initial_transcript and channels must be lists")
    seen = set()
    for channel in initial + future:
        channel_id = channel.get("id")
        if channel.get("declared") is not True:
            raise ValueError(f"undeclared channel: {channel_id}")
        if not isinstance(channel_id, str) or not channel_id or channel_id in seen:
            raise ValueError("channel ids must be unique non-empty strings")
        seen.add(channel_id)
        if type(channel.get("fresh")) is not bool:
            raise ValueError(f"channel {channel_id} must declare freshness")
        if set(channel.get("values", {})) != set(ids):
            raise ValueError(f"channel {channel_id} must define one value per world")
    return worlds, initial


def _partition(worlds: list[dict], channels: tuple[dict, ...]) -> list[dict]:
    groups = {}
    for world in worlds:
        signature = tuple(channel["values"][world["id"]] for channel in channels)
        groups.setdefault(signature, []).append(world)
    rows = []
    for signature, members in sorted(groups.items(), key=lambda item: repr(item[0])):
        common = set(members[0]["safe_progress_actions"])
        for member in members[1:]:
            common.intersection_update(member["safe_progress_actions"])
        rows.append({"transcript": list(signature), "worlds": [world["id"] for world in members],
                     "common_safe_actions": sorted(common)})
    return rows


def analyze(case: dict) -> dict:
    worlds, initial = _validate(case)
    baseline = tuple(sorted((channel for channel in initial if channel["fresh"]), key=lambda c: c["id"]))
    available = sorted((channel for channel in case["channels"] if channel["fresh"]), key=lambda c: c["id"])
    zero_rows = _partition(worlds, baseline)
    for size in range(len(available) + 1):
        for selected in itertools.combinations(available, size):
            rows = _partition(worlds, baseline + selected)
            if all(row["common_safe_actions"] for row in rows):
                return {"case_id": case["id"],
                        "decision": "PASS_NO_ADDITIONAL_EXCHANGE" if size == 0 else "PASS_METHOD_SCOPED",
                        "minimum_additional_exchanges": size,
                        "minimum_additional_channel_set": [channel["id"] for channel in selected],
                        "minimum_policy_partitions": rows,
                        "current_transcript_partitions": zero_rows}
    return {"case_id": case["id"], "decision": "HOLD_NO_FRESH_SAFE_POLICY",
            "minimum_additional_exchanges": None, "minimum_additional_channel_set": [],
            "minimum_policy_partitions": [], "current_transcript_partitions": zero_rows}


def run(cases: list[dict]) -> dict:
    return {"schema": "feedback-necessity-epistemic-candidate-v1",
            "results": [analyze(case) for case in cases]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(json.loads(args.cases.read_text(encoding="utf-8"))["cases"])
    try:
        with args.out.open("x", encoding="utf-8") as output:
            output.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except FileExistsError:
        parser.error(f"refusing to overwrite existing output: {args.out}")
    print(json.dumps({"decision": "CANDIDATE_COMPLETE", "cases": len(result["results"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
