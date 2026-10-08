#!/usr/bin/env python3
"""Deterministic no-model matched-context fixture generator for Issue #8313."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARMS = ("CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA")
DEPTHS = (0, 1, 4, 8)
QUERIES = ("CURRENT_VALUE", "BASELINE_TO_CURRENT_CHANGE")
AUTHORITY = {"execution_authority": "NONE", "observation_authority": "CURRENT_RECORD_ONLY", "schema": "fixture-v1"}


def record(task: str, query: str, depth: int, arm: str, *, position: int = 0) -> dict:
    final_value = f"value-final-{depth}"
    baseline = "value-baseline"
    history = []
    if arm == "FULL_CONFLICTING_HISTORY":
        history = [{"episode_id": f"episode-{i}", "source_id": f"source-{i}", "value": f"value-old-{i}", "status": "SUPERSEDED"} for i in range(depth)]
    elif arm == "NONCONFLICTING_HISTORY":
        history = [{"episode_id": f"neutral-{i}", "source_id": f"neutral-source-{i}", "value": f"neutral-{i:04d}", "status": "NONCONFLICTING"} for i in range(depth)]
    elif arm == "SOURCE_LINKED_DELTA" and depth:
        history = [{"episode_id": f"delta-{i}", "source_id": f"source-{i}", "from": (baseline if i == 0 else f"value-old-{i-1}"), "to": (final_value if i == depth - 1 else f"value-old-{i}"), "status": "OBSERVED_SUPERSESSION", "evidence_kind": "OBSERVED"} for i in range(depth)]
    cue = f"CURRENT_CUE:{final_value};"
    neutral = "SLOT:00000000;"
    prefix = ("POSITION_CONTROL:" + "x" * 19 + "\n") if position else ""
    body = {
        "task_id": task, "query_id": query,
        "query_text": "What is the current value?" if query == "CURRENT_VALUE" else "What changed from baseline to current?",
        "baseline": {"record_id": "baseline-0", "source_id": "source-baseline", "value": baseline},
        "current_observation": {"record_id": "current-0", "source_id": "source-current", "value": final_value},
        "authority": AUTHORITY,
        "history": history,
        "expected_information": {"current_value": final_value, "change": f"{baseline}->{final_value}"},
        "arm": arm, "depth": depth,
    }
    # Text regions deliberately have the same byte size across the four matched arms.
    # History is stored as compact JSON in a fixed-width slot; labels remain manifest-side.
    slot = json.dumps(history, sort_keys=True, separators=(",", ":"))
    slot_bytes = slot.encode("utf-8")
    budget = max(128, depth * 384)
    if len(slot_bytes) > budget:
        raise ValueError("history slot overflow")
    slot = slot + " " * (budget - len(slot_bytes))
    return {"prefix": prefix, "slot": slot, "cue": cue, "record": body}


def main() -> None:
    out = ROOT / "raw"
    out.mkdir(exist_ok=True)
    manifest = {"allocation": "5947-MULTI-UPDATE-PROVENANCE-T0-A01-20261007", "source_commit": "798ac5ad709168ff1d27b115f10f4f96b126bb71", "arms": [], "positive_control": []}
    for depth in DEPTHS:
        for query in QUERIES:
            task = f"task-depth-{depth}"
            for arm in ARMS:
                row = record(task, query, depth, arm)
                common = {k: row["record"][k] for k in ("task_id", "query_id", "query_text", "baseline", "current_observation", "authority")}
                data = (row["prefix"] + row["slot"] + "\n" + row["cue"] + "\n" + json.dumps(common, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                name = f"{task}__{query}__{arm}.bin"
                (out / name).write_bytes(data)
                cue_offset = data.index(row["cue"].encode())
                manifest["arms"].append({"task": task, "query": query, "depth": depth, "arm": arm, "file": f"raw/{name}", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "cue_offset": cue_offset, "expected_information": row["record"]["expected_information"]})
    for query in QUERIES:
        a = record("position-task", query, 4, "CURRENT_ONLY")
        b = record("position-task", query, 4, "CURRENT_ONLY", position=1)
        for label, row in (("cue-at-zero", a), ("cue-shifted", b)):
            common = {k: row["record"][k] for k in ("task_id", "query_id", "query_text", "baseline", "current_observation", "authority")}
            data = (row["prefix"] + row["slot"] + "\n" + row["cue"] + "\n" + json.dumps(common, sort_keys=True, separators=(",", ":")) + "\n").encode()
            name = f"position__{query}__{label}.bin"
            (out / name).write_bytes(data)
            manifest["positive_control"].append({"query": query, "label": label, "file": f"raw/{name}", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "cue_offset": data.index(row["cue"].encode())})
    (ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
