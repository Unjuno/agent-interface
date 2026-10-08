#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #6536 T0; imports no candidate code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def canon(x: object) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(x: object) -> str:
    return hashlib.sha256(canon(x)).hexdigest()


def covers(spans: list[list[int]], limit: int) -> bool:
    ordered = sorted((int(a), int(b)) for a, b in spans)
    end = 0
    for start, stop in ordered:
        if start > end:
            return False
        if stop > end:
            end = stop
    return end >= limit


def independently_supports(case: dict, fixture: dict) -> bool:
    media = fixture["master"]
    timeline = fixture["trace"]
    if case.get("master_ref") != media.get("asset_id"):
        return False
    if not case.get("clip_frames") or not set(case["clip_frames"]).issubset(set(media["frame_ids"])):
        return False
    spans = [entry.get("master", []) for entry in case.get("edl", [])]
    if any(len(pair) != 2 or pair[0] < 0 or pair[0] >= pair[1] or pair[1] > media["duration_ms"] for pair in spans):
        return False
    level = case.get("claim")
    if level == "SEGMENT_VISIBLE":
        return bool(spans)
    if level == "SEGMENT_TRACE_ALIGNED":
        clock = case.get("clock_override") or timeline["clock"]
        if clock.get("uncertainty_ms", 10**9) > 10 or not case.get("event_ids"):
            return False
        start, stop = spans[0]
        events = {event["id"]: event for event in timeline["events"]}
        for event_id in case["event_ids"]:
            event = events.get(event_id)
            if event is None or not start <= event["time_ms"] * clock["scale"] + clock["offset_ms"] <= stop:
                return False
        return all(row["speed"] > 0 and abs((row["clip"][1] - row["clip"][0]) * row["speed"] - (row["master"][1] - row["master"][0])) <= 1 for row in case["edl"])
    if level == "WHOLE_RUN_COVERED":
        present = {event["id"] for event in timeline["events"]}
        releases = {f"release-{event['id']}" for event in timeline["events"] if event["kind"] == "input_down" and event.get("released")}
        listed = set(case.get("event_ids", []))
        tics = case.get("tic_samples_ms", [])
        no_pause = not tics or all(0 < later - earlier <= 2500 for earlier, later in zip(tics, tics[1:]))
        return covers(spans, media["duration_ms"]) and media.get("capture_complete") is True and not media.get("gaps") and not media.get("hidden_pauses") and timeline.get("coverage_complete") is True and not timeline.get("gaps") and present.issubset(listed) and releases.issubset(listed) and not case.get("dropped_event_ids") and no_pause
    if level == "TASK_OUTCOME_VERIFIED":
        receipt = media.get("terminal", {})
        return case.get("claim_outcome") == "clear" and receipt.get("outcome") == "clear" and receipt.get("scorer") == "independent-score-v1" and receipt.get("master_asset_id") == media.get("asset_id") and covers(spans, media["duration_ms"])
    if level == "LOCAL_CONTROL_DURING_MODEL_WAIT":
        attribution = case.get("control_attribution") or {}
        interval = attribution.get("input_interval")
        if not interval or attribution.get("input_actor") != "controller" or not attribution.get("visible_movement"):
            return False
        return any(max(interval[0], left) < min(interval[1], right) for left, right in timeline["model_waits"])
    return False


def audit(raw: dict, fixture: dict, oracle: dict) -> dict:
    errors: list[str] = []
    expected_fixture = hashlib.sha256((ROOT / "fixtures.json").read_bytes()).hexdigest()
    if raw.get("schema") != "clip-trace-raw-v1" or raw.get("fixture_digest") != expected_fixture:
        errors.append("fixture_identity_mismatch")
    if raw.get("master_digest") != digest(fixture["master"]):
        errors.append("master_digest_mismatch")
    cases = {case["id"]: case for case in fixture["cases"]}
    rows = {row.get("case_id"): row for row in raw.get("rows", [])}
    if set(rows) != set(cases) or len(rows) != len(raw.get("rows", [])):
        errors.append("case_cardinality_mismatch")
    false_accepts: dict[str, int] = {}
    d_false_accepts = 0
    positives = 0
    arm_names = ("A_clip_caption", "B_clip_master_link", "C_hashed_edl_only", "D_claim_scoped_map_candidate")
    for case_id, case in cases.items():
        row = rows.get(case_id)
        if row is None:
            continue
        computed = independently_supports(case, fixture)
        truth = computed and oracle["supported"].get(case_id) is True
        positives += int(truth)
        for arm in arm_names:
            accepted = row.get("arms", {}).get(arm)
            if accepted is None:
                errors.append(f"missing_arm:{case_id}:{arm}")
            elif accepted and not truth:
                false_accepts[arm] = false_accepts.get(arm, 0) + 1
                if arm == "D_claim_scoped_map_candidate":
                    d_false_accepts += 1
        if row.get("arms", {}).get("D_claim_scoped_map_candidate") is not computed:
            errors.append(f"independent_decision_mismatch:{case_id}")
        if row.get("master_digest") != digest(fixture["master"]) or row.get("edl_digest") != digest(case["edl"]):
            errors.append(f"source_digest_mismatch:{case_id}")
        if row.get("event_ids") != case.get("event_ids"):
            errors.append(f"event_lineage_mismatch:{case_id}")
    if d_false_accepts:
        errors.append("unsupported_claim_accepted_by_D")
    if positives != 2:
        errors.append("positive_denominator_mismatch")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "cases": len(cases), "scoped_positive_accepts": positives, "false_accepts_by_arm": false_accepts, "errors": errors}


def mutation_rejected(name: str, raw: dict, fixture: dict, oracle: dict) -> bool:
    changed = json.loads(json.dumps(raw))
    if name == "forged_master_digest":
        changed["master_digest"] = "0" * 64
    elif name == "unmapped_interval":
        changed["rows"][0]["edl_digest"] = "f" * 64
    elif name == "shifted_clock_receipt":
        changed["rows"][1]["arms"]["D_claim_scoped_map_candidate"] = False
    elif name == "missing_release_record":
        changed["rows"][5]["event_ids"] = []
    elif name == "false_clear_receipt":
        changed["rows"][7]["arms"]["D_claim_scoped_map_candidate"] = True
    else:
        raise ValueError(name)
    return bool(audit(changed, fixture, oracle)["errors"])


def main() -> None:
    fixture = json.loads((ROOT / "fixtures.json").read_text())
    oracle = json.loads((ROOT / "oracle.json").read_text())
    raw = json.loads((ROOT / "RAW.json").read_text())
    result = audit(raw, fixture, oracle)
    result["mutations"] = {name: mutation_rejected(name, raw, fixture, oracle) for name in oracle["required_mutations"]}
    if not all(result["mutations"].values()):
        result["status"] = "FAIL_AUDITOR_MUTATION_CONTROL"
    (ROOT / "AUDIT.json").write_bytes(canon(result) + b"\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
