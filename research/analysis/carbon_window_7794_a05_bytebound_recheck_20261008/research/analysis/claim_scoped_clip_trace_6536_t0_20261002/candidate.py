#!/usr/bin/env python3
"""Frozen synthetic evidence-arm candidate for Issue #6536 T0."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLAIMS = {"SEGMENT_VISIBLE", "SEGMENT_TRACE_ALIGNED", "WHOLE_RUN_COVERED", "TASK_OUTCOME_VERIFIED", "LOCAL_CONTROL_DURING_MODEL_WAIT"}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def union_covers(intervals: list[list[int]], start: int, end: int) -> bool:
    cursor = start
    for left, right in sorted(intervals):
        if right <= cursor:
            continue
        if left > cursor:
            return False
        cursor = max(cursor, right)
        if cursor >= end:
            return True
    return cursor >= end


def claim_scope(case: dict, fixture: dict) -> bool:
    claim = case["claim"]
    master = fixture["master"]
    if claim not in CLAIMS:
        return False
    if case["master_ref"] != master["asset_id"]:
        return False
    if not case["clip_frames"] or any(frame not in master["frame_ids"] for frame in case["clip_frames"]):
        return False
    spans = [row["master"] for row in case["edl"]]
    if claim == "SEGMENT_VISIBLE":
        return all(0 <= a < b <= master["duration_ms"] for a, b in spans)
    if claim == "SEGMENT_TRACE_ALIGNED":
        clock = case.get("clock_override") or fixture["trace"]["clock"]
        events = {event["id"]: event for event in fixture["trace"]["events"]}
        if clock["uncertainty_ms"] > 10 or not case["event_ids"]:
            return False
        for row in case["edl"]:
            clip_duration = row["clip"][1] - row["clip"][0]
            master_duration = row["master"][1] - row["master"][0]
            if row["speed"] <= 0 or abs(clip_duration * row["speed"] - master_duration) > 1:
                return False
            for event_id in case["event_ids"]:
                event = events.get(event_id)
                if event and not row["master"][0] <= event["time_ms"] * clock["scale"] + clock["offset_ms"] <= row["master"][1]:
                    return False
        return True
    if claim == "WHOLE_RUN_COVERED":
        tic_samples = case.get("tic_samples_ms", [])
        continuity_ok = not tic_samples or all(0 < b - a <= 2500 for a, b in zip(tic_samples, tic_samples[1:]))
        required = {event["id"] for event in fixture["trace"]["events"]}
        required.update(f"release-{event['id']}" for event in fixture["trace"]["events"] if event["kind"] == "input_down" and event.get("released"))
        return union_covers(spans, 0, master["duration_ms"]) and master["capture_complete"] and not master["gaps"] and not master["hidden_pauses"] and not fixture["trace"]["gaps"] and fixture["trace"]["coverage_complete"] and continuity_ok and required.issubset(set(case["event_ids"])) and not case.get("dropped_event_ids")
    if claim == "TASK_OUTCOME_VERIFIED":
        return union_covers(spans, 0, master["duration_ms"]) and case.get("claim_outcome") == master["terminal"]["outcome"] == "clear" and master["terminal"]["scorer"] == "independent-score-v1"
    if claim == "LOCAL_CONTROL_DURING_MODEL_WAIT":
        attribution = case.get("control_attribution") or {}
        interval = attribution.get("input_interval")
        return bool(attribution.get("visible_movement") and attribution.get("input_actor") == "controller" and interval and any(max(interval[0], wait[0]) < min(interval[1], wait[1]) for wait in fixture["trace"]["model_waits"]))
    return False


def run(fixture: dict) -> dict:
    master_digest = sha(fixture["master"])
    rows = []
    for case in fixture["cases"]:
        mapped_frames = all(frame in fixture["master"]["frame_ids"] for frame in case["clip_frames"])
        edl_valid = case["master_ref"] == fixture["master"]["asset_id"] and mapped_frames and all(0 <= row["master"][0] < row["master"][1] <= fixture["master"]["duration_ms"] for row in case["edl"])
        rows.append({
            "case_id": case["id"],
            "claim": case["claim"],
            "arms": {
                "A_clip_caption": bool(case["caption"]),
                "B_clip_master_link": bool(case["caption"]) and mapped_frames,
                "C_hashed_edl_only": edl_valid and case["claim"] in {"SEGMENT_VISIBLE", "WHOLE_RUN_COVERED"} and (case["claim"] != "WHOLE_RUN_COVERED" or union_covers([row["master"] for row in case["edl"]], 0, fixture["master"]["duration_ms"])),
                "D_claim_scoped_map_candidate": claim_scope(case, fixture),
            },
            "master_digest": master_digest,
            "edl_digest": sha(case["edl"]),
            "mapped_frame_count": sum(frame in fixture["master"]["frame_ids"] for frame in case["clip_frames"]),
            "event_ids": list(case["event_ids"]),
        })
    return {"schema": "clip-trace-raw-v1", "fixture_digest": hashlib.sha256((ROOT / "fixtures.json").read_bytes()).hexdigest(), "master_digest": master_digest, "rows": rows}


def main() -> None:
    fixture = json.loads((ROOT / "fixtures.json").read_text())
    raw = run(fixture)
    (ROOT / "RAW.json").write_bytes(canonical(raw) + b"\n")
    print(json.dumps({"candidate_rows": len(raw["rows"]), "fixture_digest": raw["fixture_digest"], "master_digest": raw["master_digest"]}, sort_keys=True))


if __name__ == "__main__":
    main()
