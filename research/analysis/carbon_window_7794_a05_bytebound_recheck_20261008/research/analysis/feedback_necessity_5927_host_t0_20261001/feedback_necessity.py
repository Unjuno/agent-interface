"""Finite, task/channel-relative feedback-necessity construction probe."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def validate_case(case: dict) -> None:
    worlds = case.get("worlds")
    if not isinstance(worlds, list) or len(worlds) < 2:
        raise ValueError("case requires at least two worlds")
    ids = [world.get("id") for world in worlds]
    if any(not isinstance(value, str) or not value for value in ids) or len(set(ids)) != len(ids):
        raise ValueError("world ids must be unique non-empty strings")
    for world in worlds:
        actions = world.get("safe_progress_actions")
        if not isinstance(actions, list) or any(not isinstance(a, str) or not a for a in actions):
            raise ValueError("safe_progress_actions must be a string list")
    channel_ids = set()
    for channel in case.get("channels", []):
        if not channel.get("declared", False):
            raise ValueError(f"undeclared channel: {channel.get('id')}")
        channel_id = channel.get("id")
        if not isinstance(channel_id, str) or not channel_id or channel_id in channel_ids:
            raise ValueError("channel ids must be unique non-empty strings")
        channel_ids.add(channel_id)
        if set(channel.get("values", {})) != set(ids):
            raise ValueError(f"channel {channel_id} must define one value per world")
        if type(channel.get("fresh")) is not bool:
            raise ValueError(f"channel {channel_id} must declare freshness")


def _intersection(worlds: list[dict]) -> list[str]:
    common = set(worlds[0]["safe_progress_actions"])
    for world in worlds[1:]:
        common.intersection_update(world["safe_progress_actions"])
    return sorted(common)


def _safe_for_subset(case: dict, selected: tuple[dict, ...]) -> tuple[bool, list[dict]]:
    partitions: dict[tuple, list[dict]] = {}
    for world in case["worlds"]:
        signature = tuple(channel["values"][world["id"]] for channel in selected)
        partitions.setdefault(signature, []).append(world)
    witnesses = []
    for signature, worlds in sorted(partitions.items(), key=lambda item: repr(item[0])):
        common = _intersection(worlds)
        witnesses.append({"transcript": list(signature), "worlds": [w["id"] for w in worlds], "common_safe_actions": common})
        if not common:
            return False, witnesses
    return True, witnesses


def analyze_case(case: dict) -> dict:
    validate_case(case)
    channels = sorted((c for c in case.get("channels", []) if c["fresh"]), key=lambda c: c["id"])
    for count in range(len(channels) + 1):
        for selected in itertools.combinations(channels, count):
            safe, partitions = _safe_for_subset(case, selected)
            if safe:
                if count == 0:
                    decision = "PASS_NULL_NO_LOWER_BOUND"
                else:
                    decision = "PASS_METHOD_SCOPED"
                return {
                    "case_id": case["id"], "decision": decision,
                    "minimum_exchanges": count,
                    "minimum_channel_set": [c["id"] for c in selected],
                    "minimum_policy_partitions": partitions,
                    "zero_exchange_witness": _safe_for_subset(case, ())[1][0],
                }
    return {
        "case_id": case["id"], "decision": "HOLD_NO_FRESH_DISTINGUISHING_CHANNEL",
        "minimum_exchanges": None, "minimum_channel_set": [],
        "minimum_policy_partitions": [],
        "zero_exchange_witness": _safe_for_subset(case, ())[1][0],
    }


def run_candidate(cases: list[dict]) -> dict:
    return {"schema": "feedback-necessity-candidate-v1", "results": [analyze_case(case) for case in cases]}


def audit_result(cases: list[dict], candidate: dict) -> dict:
    """Independent raw-only re-enumeration; intentionally does not call analyze_case."""
    errors = []
    expected = []
    for case in cases:
        try:
            validate_case(case)
        except (ValueError, TypeError) as error:
            errors.append(f"invalid_frozen_case:{case.get('id')}:{error}")
            continue
        for world in case["worlds"]:
            if world.get("safe_progress_actions") != world.get("oracle_safe_progress_actions"):
                errors.append(f"oracle_action_mismatch:{case['id']}:{world['id']}")
        available = [item for item in case.get("channels", []) if item.get("fresh") is True]
        available.sort(key=lambda item: item["id"])
        answer = None
        for width in range(len(available) + 1):
            if answer is not None:
                break
            for group in itertools.combinations(available, width):
                transcript_groups = {}
                for world in case["worlds"]:
                    key = tuple(item["values"][world["id"]] for item in group)
                    transcript_groups.setdefault(key, []).append(world)
                viable = True
                checked_groups = []
                for key, states in transcript_groups.items():
                    joint = set(states[0]["safe_progress_actions"])
                    for state in states[1:]:
                        joint = joint & set(state["safe_progress_actions"])
                    if not joint:
                        viable = False
                    checked_groups.append({"transcript": list(key), "worlds": [s["id"] for s in states], "common_safe_actions": sorted(joint)})
                if viable:
                    zero_groups = {}
                    for world in case["worlds"]:
                        zero_groups.setdefault((), []).append(world)
                    only_group = list(zero_groups.values())[0]
                    common = set(only_group[0]["safe_progress_actions"])
                    for world in only_group[1:]:
                        common.intersection_update(world["safe_progress_actions"])
                    answer = {
                        "case_id": case["id"],
                        "decision": "PASS_NULL_NO_LOWER_BOUND" if width == 0 else "PASS_METHOD_SCOPED",
                        "minimum_exchanges": width,
                        "minimum_channel_set": [item["id"] for item in group],
                        "minimum_policy_partitions": checked_groups,
                        "zero_exchange_witness": {"transcript": [], "worlds": [s["id"] for s in only_group], "common_safe_actions": sorted(common)},
                    }
                    break
        if answer is None:
            worlds = case["worlds"]
            common = set(worlds[0]["safe_progress_actions"])
            for world in worlds[1:]:
                common.intersection_update(world["safe_progress_actions"])
            answer = {
                "case_id": case["id"], "decision": "HOLD_NO_FRESH_DISTINGUISHING_CHANNEL",
                "minimum_exchanges": None, "minimum_channel_set": [],
                "minimum_policy_partitions": [],
                "zero_exchange_witness": {"transcript": [], "worlds": [s["id"] for s in worlds], "common_safe_actions": sorted(common)},
            }
        expected.append(answer)
    actual = candidate.get("results") if isinstance(candidate, dict) else None
    if actual != expected:
        errors.append("minimum_exchanges")
    return {"schema": "feedback-necessity-audit-v1", "status": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT", "errors": errors, "independently_recomputed": expected}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    payload = run_candidate(_load(args.cases)["cases"])
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": "CANDIDATE_COMPLETE", "cases": len(payload["results"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(candidate_main())
