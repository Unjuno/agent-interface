"""Finite synthetic input/output conformance probe for Issue #5518.

No GUI, model, provider, or runtime adapter is involved. The frozen output
alphabet makes UNKNOWN explicit; missing output is a distinct observation.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


TRANSITIONS = {
    ("EMPTY", "OBSERVE_CURRENT"): {"CURRENT": "FRESH", "UNKNOWN": "UNKNOWN"},
    ("EMPTY", "OBSERVE_STALE"): {"STALE": "STALE", "UNKNOWN": "UNKNOWN"},
    ("FRESH", "OBSERVE_CURRENT"): {"CURRENT": "FRESH", "UNKNOWN": "UNKNOWN"},
    ("FRESH", "ADMIT"): {"ADMITTED": "ACTIVE", "REFUSED": "FRESH"},
    ("STALE", "ADMIT"): {"REFUSED": "STALE", "UNKNOWN": "STALE"},
    ("UNKNOWN", "ADMIT"): {"REFUSED": "UNKNOWN", "UNKNOWN": "UNKNOWN"},
    ("ACTIVE", "VERIFY_SUCCESS"): {"EFFECT_CONFIRMED": "EFFECT_CONFIRMED", "UNKNOWN": "ACTIVE"},
    ("ACTIVE", "VERIFY_FAILURE"): {"EFFECT_NOT_CONFIRMED": "ACTIVE", "UNKNOWN": "ACTIVE"},
    ("ACTIVE", "RELEASE"): {"RELEASED_EMPTY": "EMPTY", "UNKNOWN": "ACTIVE"},
    ("EFFECT_CONFIRMED", "RELEASE"): {"RELEASED_EMPTY": "EMPTY", "UNKNOWN": "EFFECT_CONFIRMED"},
    ("ACTIVE", "CANCEL"): {"CANCELLED_EMPTY": "EMPTY", "UNKNOWN": "ACTIVE"},
}


TRACES = {
    "conforming_hidden_batch_retry": [
        ("OBSERVE_CURRENT", "CURRENT"),
        ("ADMIT", "ADMITTED"),
        ("VERIFY_SUCCESS", "EFFECT_CONFIRMED"),
        ("RELEASE", "RELEASED_EMPTY"),
    ],
    "target_mutation": [("OBSERVE_CURRENT", "DECOY")],
    "stale_unauthorized": [
        ("OBSERVE_STALE", "STALE"),
        ("ADMIT", "ADMITTED"),
    ],
    "semantic_failure_reported_success": [("OBSERVE_CURRENT", "CURRENT"), ("ADMIT", "ADMITTED"), ("VERIFY_FAILURE", "EFFECT_CONFIRMED")],
    "delayed_explicit_unknown": [
        ("OBSERVE_CURRENT", "UNKNOWN"),
        ("ADMIT", "REFUSED"),
    ],
    "silent_missing_output": [("OBSERVE_CURRENT", "<NO_OUTPUT>")],
}


def check(name: str, trace: list[tuple[str, str]]) -> dict:
    history: list[dict[str, str]] = []
    counterexample = None
    state = "EMPTY"
    for index, (step_name, actual) in enumerate(trace, start=1):
        allowed_transitions = TRANSITIONS.get((state, step_name), {})
        history.append({"input": step_name, "output": actual})
        if actual not in allowed_transitions:
            counterexample = {
                "prefix_length": index,
                "state_before": state,
                "input_history": history.copy(),
                "step": step_name,
                "allowed_outputs": sorted(allowed_transitions),
                "actual_output": actual,
            }
            break
        state = allowed_transitions[actual]
    accepted = counterexample is None
    expected = {
        "conforming_hidden_batch_retry": True,
        "target_mutation": False,
        "stale_unauthorized": False,
        "semantic_failure_reported_success": False,
        "delayed_explicit_unknown": True,
        "silent_missing_output": False,
    }[name]
    return {
        "scenario": name,
        "accepted": accepted,
        "expected_accepted": expected,
        "match": accepted is expected,
        "counterexample": counterexample,
        "terminal_state": state,
        "internal_hidden_transitions": ["BATCH", "RETRY"],
        "external_trace": [
            {"input": s, "output": output}
            for s, output in trace[: counterexample["prefix_length"] if counterexample else None]
        ],
    }


def main() -> int:
    results = [check(name, trace) for name, trace in TRACES.items()]
    payload = {
        "study": "issue-5518-ioco-t0-v1",
        "scope": "finite synthetic output-inclusion check; not GUI conformance",
        "alphabet_version": "frozen-v1",
        "quiescence_policy": "explicit UNKNOWN is allowed where listed; missing output is forbidden",
        "results": results,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    output_path = os.environ.get("RESULT_PATH")
    if output_path:
        Path(output_path).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if all(row["match"] for row in results) else 1


if __name__ == "__main__":
    sys.exit(main())

