#!/usr/bin/env python3
"""Independent raw-byte auditor; does not import candidate generator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ARMS = {"CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA"}
EXPECTED_DEPTHS = {0, 1, 4, 8}
EXPECTED_QUERIES = {"CURRENT_VALUE", "BASELINE_TO_CURRENT_CHANGE"}


def audit_path(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = json.loads((root / "manifest.json").read_text())
    rows = manifest["arms"]
    if len(rows) != 32:
        errors.append("ARM_COUNT")
    groups: dict[tuple[str, str, int], list[tuple[dict, bytes]]] = {}
    for row in rows:
        raw = (root / row["file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["bytes"]:
            errors.append("HASH_OR_LENGTH")
        cue = b"CURRENT_CUE:"
        offset = raw.index(cue) if cue in raw else -1
        if offset != row["cue_offset"]:
            errors.append("CUE_OFFSET")
        expected_offset = max(128, row["depth"] * 384) + 1
        if offset != expected_offset:
            errors.append("FROZEN_CUE_POSITION")
        try:
            prefix_len = 39 if raw.startswith(b"POSITION_CONTROL:") else 0
            slot_end = raw.index(b"\n", prefix_len)
            history = json.loads(raw[prefix_len:slot_end].rstrip())
            payload = json.loads(raw[slot_end + 1:].split(b"\n", 1)[1])
        except Exception:
            errors.append("RAW_RECORD_PARSE")
            continue
        if payload["task_id"] != row["task"] or payload["query_id"] != row["query"]:
            errors.append("MANIFEST_BINDING")
        expected_history_depth = 0 if row["arm"] == "CURRENT_ONLY" else row["depth"]
        if len(history) != expected_history_depth:
            errors.append("HISTORY_DEPTH")
        if row["arm"] == "FULL_CONFLICTING_HISTORY" and any(x.get("status") != "SUPERSEDED" for x in history):
            errors.append("CONFLICT_LABEL")
        if row["arm"] == "NONCONFLICTING_HISTORY" and any(x.get("status") != "NONCONFLICTING" for x in history):
            errors.append("NEUTRAL_LABEL")
        if row["arm"] == "SOURCE_LINKED_DELTA" and any(not x.get("source_id") or x.get("status") != "OBSERVED_SUPERSESSION" for x in history):
            errors.append("DELTA_PROVENANCE")
        if row["arm"] == "SOURCE_LINKED_DELTA":
            expected_chain = [("value-baseline" if i == 0 else f"value-old-{i-1}", row["expected_information"]["current_value"] if i == row["depth"] - 1 else f"value-old-{i}") for i in range(row["depth"])]
            observed_chain = [(x.get("from"), x.get("to")) for x in history]
            if observed_chain != expected_chain or any(x.get("episode_id") != f"delta-{i}" or x.get("source_id") != f"source-{i}" or x.get("evidence_kind") != "OBSERVED" for i, x in enumerate(history)):
                errors.append("DELTA_LINEAGE")
        if row["arm"] == "FULL_CONFLICTING_HISTORY" and any(x.get("episode_id") != f"episode-{i}" or x.get("source_id") != f"source-{i}" for i, x in enumerate(history)):
            errors.append("CONFLICT_LINEAGE")
        if payload["authority"] != {"execution_authority": "NONE", "observation_authority": "CURRENT_RECORD_ONLY", "schema": "fixture-v1"}:
            errors.append("AUTHORITY")
        if payload["current_observation"]["value"] != row["expected_information"]["current_value"]:
            errors.append("CURRENT_TRUTH")
        expected_cue = f"CURRENT_CUE:{row['expected_information']['current_value']};".encode("utf-8")
        if expected_cue not in raw:
            errors.append("CURRENT_CUE_TRUTH")
        if payload["baseline"]["value"] != "value-baseline":
            errors.append("BASELINE")
        groups.setdefault((row["task"], row["query"], row["depth"]), []).append((row, raw, history))
    for (task, query, depth), members in groups.items():
        if {r["arm"] for r, _, _ in members} != EXPECTED_ARMS:
            errors.append("ARM_SET")
        if len({len(raw) for _, raw, _ in members}) != 1 or len({raw.index(b"CURRENT_CUE:") for _, raw, _ in members}) != 1:
            errors.append("MATCHED_LENGTH_OR_OFFSET")
        parsed = []
        for _, raw, history in members:
            slot_end = raw.index(b"\n")
            parsed.append((json.loads(raw[slot_end + 1:].split(b"\n", 1)[1]), history))
        if len({p[0]["task_id"] for p in parsed}) != 1 or len({p[0]["query_text"] for p in parsed}) != 1:
            errors.append("MATCHED_TASK_QUERY")
        if len({json.dumps(p[0]["current_observation"], sort_keys=True) for p in parsed}) != 1 or len({json.dumps(p[0]["authority"], sort_keys=True) for p in parsed}) != 1:
            errors.append("MATCHED_TRUTH_AUTHORITY")
        if query == "BASELINE_TO_CURRENT_CHANGE" and any(p[0]["baseline"]["record_id"] != "baseline-0" for p in parsed):
            errors.append("HISTORY_REQUIRED_BASELINE")
        if depth == 0 and any(history for _, history in parsed):
            errors.append("DEPTH_ZERO_HISTORY")
    if {r["depth"] for r in rows} != EXPECTED_DEPTHS or {r["query"] for r in rows} != EXPECTED_QUERIES:
        errors.append("DEPTH_OR_QUERY_SCHEDULE")
    controls = manifest["positive_control"]
    if len(controls) != 4:
        errors.append("POSITIVE_CONTROL_COUNT")
    for query in EXPECTED_QUERIES:
        pair = [x for x in controls if x["query"] == query]
        if len(pair) != 2 or len({x["cue_offset"] for x in pair}) != 2:
            errors.append("POSITION_CONTROL")
        for row in pair:
            raw = (root / row["file"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != row["sha256"] or len(raw) != row["bytes"] or raw.index(b"CURRENT_CUE:") != row["cue_offset"]:
                errors.append("POSITION_CONTROL_RAW")
    return errors


def audit(path: Path) -> list[str]:
    return audit_path(path.parent)


def main() -> None:
    errors = audit(ROOT / "manifest.json")
    print(json.dumps({"result": "PASS" if not errors else "FAIL", "errors": errors}, sort_keys=True))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()
