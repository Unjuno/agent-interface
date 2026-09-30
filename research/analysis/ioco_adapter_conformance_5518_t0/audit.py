"""Independent raw-only audit for the #5518 finite conformance spike."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "reference-direct": "CONFORMANT",
    "reference-hidden-batch-retry": "CONFORMANT",
    "forbidden-target-switch": "NONCONFORMANT",
    "forbidden-stale-admission": "NONCONFORMANT",
    "forbidden-unauthorized-admission": "NONCONFORMANT",
    "forbidden-semantic-false-success": "NONCONFORMANT",
    "delayed-unknown-and-explicit-quiescence": "CONFORMANT",
    "missing-output-is-not-quiescence": "UNKNOWN",
}


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def evaluate_independently(spec, trace):
    """Auditor-owned transition walk, intentionally not importing contract.py."""
    state = spec["initial"]
    for position, exchange in enumerate(trace, 1):
        selected = [t for t in spec["transitions"]
                    if t["from"] == state and _canon(t["input"]) == _canon(exchange["input"])]
        if len(selected) != 1:
            why = "INPUT_NOT_SPECIFIED" if not selected else "AMBIGUOUS_SPEC_TRANSITION"
            return {"status": "NONCONFORMANT", "reason": why,
                    "counterexample": {"prefix_length": position, "index": position,
                                       "state": state, "input": exchange["input"],
                                       "observed_outputs": exchange.get("outputs", []),
                                       "allowed_outputs": [], "reason": why}}
        transition = selected[0]
        actual = exchange.get("outputs")
        if not isinstance(actual, list) or len(actual) == 0:
            return {"status": "UNKNOWN", "reason": "MISSING_OUTPUT_NOT_QUIESCENCE",
                    "prefix_length": position, "state": state, "input": exchange["input"]}
        permitted = transition["allowed_outputs"]
        if len(actual) != 1 or all(_canon(actual[0]) != _canon(item) for item in permitted):
            