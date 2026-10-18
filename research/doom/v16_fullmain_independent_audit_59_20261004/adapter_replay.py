#!/usr/bin/env python3
"""Replay retained V16 one-hold producer rows through the pinned V15 adapter."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any

from audit import ONE_HOLD

PACKAGE = Path(__file__).resolve().parent
PIN = PACKAGE / "dependency/SOURCE_PINS.json"
ADAPTER_DIR = PACKAGE / "dependency/attribution_adapter_t2"
INPUT_DIR = ONE_HOLD / "out/session"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(repo: Path) -> dict[str, Any]:
    pin = _json(PIN)
    source_dir = PACKAGE / "dependency"
    actual_hashes = {
        "adapter.py": hashlib.sha256((ADAPTER_DIR / "adapter.py").read_bytes()).hexdigest(),
        "scorer_feedback_attribution_v1.py": hashlib.sha256((source_dir / "scorer_feedback_attribution_v1.py").read_bytes()).hexdigest(),
    }
    if actual_hashes != pin.get("files"):
        raise ValueError("pinned_adapter_source_hash_mismatch")
    sys.path.insert(0, str(ADAPTER_DIR))
    adapter = importlib.import_module("adapter")
    session = repo / INPUT_DIR
    samples = _jsonl(session / "scorer-samples.jsonl")
    all_events = _jsonl(session / "events.jsonl")
    input_rows = [row for row in all_events if row.get("event") in {"input_admission", "input_release_transition"}]
    result = adapter.adapt_session_records(samples, [], input_rows)
    summary = _json(session / "scorer-summary.json")
    transition = next((row for row in input_rows if row.get("event") == "input_release_transition"), {})
    return {
        "adapter_head": pin["source_head"],
        "adapter_source_sha256": actual_hashes,
        "trace_integrity": result["trace_integrity"],
        "counts": result["counts"],
        "attributions": result["attributions"],
        "source_summary": {
            "sample_count": summary.get("sample_count"),
            "event_count": summary.get("event_count"),
            "positive_useful_events": summary.get("event_summary", {}).get("positive_useful_events"),
        },
        "release_identity": {key: transition.get(key) for key in ("id", "step", "owner_id", "intent_token", "key", "release_batch_identifier", "physical_verification_authoritative")},
        "interpretation": "The adapter joins the actual retained admission and synchronized release receipt. Its release_sync_ns is an owner XSync boundary with physical_verification_authoritative=false; this does not certify physical key-up timing. Zero actual positive scorer events means attribution was not exercised.",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=PACKAGE.parents[3])
    args = parser.parse_args()
    print(json.dumps(run(args.repo), indent=2, sort_keys=True))
