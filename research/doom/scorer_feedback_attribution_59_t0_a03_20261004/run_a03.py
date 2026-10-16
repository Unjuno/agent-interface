"""Capture the fixed endpoint-tie comparison without external resources."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from scorer_feedback_attribution_v2 import attribute_positive_events


ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "scorer_feedback_attribution_59_t0_a01_20261004" / "scorer_feedback_attribution_v1.py"


def load_old():
    spec = importlib.util.spec_from_file_location("a01_attribution", OLD)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.attribute_positive_events


def sample_rows():
    return [{"schema": "independent-progress-sample-v2", "sample_ns": t} for t in (100, 200)]


def event():
    return {"schema": "independent-progress-event-v2", "event_sequence": 1,
            "observed_ns": 200, "kind": "KILL_COUNT_INCREASE", "polarity": "positive",
            "useful": True, "controller_visible": False}


def interval(start, end):
    return {"intent_token": "intent-a", "key": "ATTACK", "admitted_ns": start,
            "release_sync_ns": end, "release_verified": True}


def main():
    old = load_old()
    cases = {"admission_tied_to_lower": interval(100, 210),
             "release_tied_to_upper": interval(90, 200),
             "strictly_bracketed": interval(90, 210)}
    rows = {}
    for name, action in cases.items():
        input_rows = [sample_rows(), [event()], [action]]
        rows[name] = {"a01": old(*input_rows), "a03": attribute_positive_events(*input_rows)}
    result = {"schema": "scorer-feedback-attribution-a03-result-v1", "cases": rows,
              "command": "python run_a03.py", "causal_attribution": "NOT_ESTABLISHED"}
    Path("RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
