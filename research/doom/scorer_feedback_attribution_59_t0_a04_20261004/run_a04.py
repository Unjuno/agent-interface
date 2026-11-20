"""Compare saved malformed-kind cases against A03 and the A04 successor."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from scorer_feedback_attribution_v3 import attribute_positive_events


HERE = Path(__file__).resolve().parent
A03_PATH = HERE.parent / "scorer_feedback_attribution_59_t0_a03_20261004" / "scorer_feedback_attribution_v2.py"


def load_a03():
    spec = importlib.util.spec_from_file_location("a03_candidate", A03_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.attribute_positive_events


def samples():
    return [{"schema": "independent-progress-sample-v2", "sample_ns": t} for t in (100, 200)]


def main():
    a03 = load_a03()
    cases = {"missing": None, "null": None, "empty": "", "whitespace": "   ", "non_string": 17}
    results = {}
    for label, kind in cases.items():
        event = {"schema": "independent-progress-event-v2", "event_sequence": 1,
                 "observed_ns": 200, "polarity": "positive", "useful": True,
                 "controller_visible": False}
        if label != "missing":
            event["kind"] = kind
        rows = [{"intent_token": "intent-a", "key": "ATTACK", "admitted_ns": 90,
                 "release_sync_ns": 210, "release_verified": True}]
        inputs = (samples(), [event], rows)
        old = a03(*inputs)
        try:
            attribute_positive_events(*inputs)
        except ValueError as error:
            new = {"rejected": True, "error": str(error)}
        else:
            new = {"rejected": False}
        results[label] = {"a03": old, "a04": new}

    valid = {"schema": "independent-progress-event-v2", "event_sequence": 2,
             "observed_ns": 200, "kind": "KILL_COUNT_INCREASE", "polarity": "positive",
             "useful": True, "controller_visible": False}
    valid_rows = [{"intent_token": "intent-a", "key": "ATTACK", "admitted_ns": 90,
                   "release_sync_ns": 210, "release_verified": True}]
    results["valid_control"] = {
        "a03": a03(samples(), [valid], valid_rows),
        "a04": attribute_positive_events(samples(), [valid], valid_rows),
    }
    result = {"schema": "scorer-feedback-attribution-a04-result-v1", "cases": results,
              "command": "python run_a04.py", "scope": "synthetic schema-boundary construction"}
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
