#!/usr/bin/env python3
"""Run pinned baseline and repaired adapter on retained visual03 producer rows."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T2 = HERE.parent


def jsonl(name):
    return [json.loads(line) for line in (HERE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def load_pre_fix():
    path = HERE / "pre_fix_adapter.py"
    spec = importlib.util.spec_from_file_location("visual03_pre_fix_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    pin = json.loads((HERE / "SOURCE_PINS.json").read_text(encoding="utf-8"))
    adapter_file = T2 / "adapter.py"
    t0_file = T2.parent / "scorer_feedback_attribution_v1.py"
    actual = {
        "baseline_adapter_sha256": hashlib.sha256((HERE / "pre_fix_adapter.py").read_bytes()).hexdigest(),
        "candidate_adapter_sha256": hashlib.sha256(adapter_file.read_bytes()).hexdigest(),
        "scorer_feedback_attribution_v1_sha256": hashlib.sha256(t0_file.read_bytes()).hexdigest(),
    }
    if actual["baseline_adapter_sha256"] != pin["baseline_adapter"]["sha256"]:
        raise SystemExit("baseline_adapter_hash_mismatch")
    if actual["candidate_adapter_sha256"] != pin["candidate_adapter_sha256"]:
        raise SystemExit("candidate_adapter_hash_mismatch")

    sys.path.insert(0, str(T2))
    from adapter import adapt_session_records

    samples = jsonl("scorer-samples.jsonl")
    events = jsonl("scorer-events.jsonl")
    inputs = jsonl("input-rows.jsonl")
    baseline = load_pre_fix().adapt_session_records(samples, events, inputs)
    candidate = adapt_session_records(samples, events, inputs)
    result = {
        "schema": "issue59-v16-visual03-adapter-replay-result-v1",
        "adapter_source_hashes": actual,
        "raw_counts": {"samples": len(samples), "events": len(events), "input_rows": len(inputs)},
        "baseline": baseline,
        "candidate": candidate,
        "disposition": "PASS_SCOPED_STEP_SCOPED_BATCH_REPLAY" if (
            baseline["trace_integrity"] == "HOLD_INCOMPLETE_RELEASE_BATCH"
            and candidate["trace_integrity"] == "SOURCE_ROWS_JOINED"
            and candidate["attributions"]
            and candidate["attributions"][0]["status"] == "TEMPORALLY_UNIQUE"
            and candidate["attributions"][0]["causal_attribution"] == "NOT_ESTABLISHED"
        ) else "HOLD_OR_FAIL_VISUAL03_ADAPTER_REPLAY",
        "scope": "One retained visual03 scorer event; owner XSync release boundary is not physical key-up timing. No causal, task-effect, recovery, or live-run qualification.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["disposition"] == "PASS_SCOPED_STEP_SCOPED_BATCH_REPLAY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
