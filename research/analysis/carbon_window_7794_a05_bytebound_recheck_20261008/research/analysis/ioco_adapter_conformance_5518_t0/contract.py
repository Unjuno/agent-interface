"""Finite input-conditioned output-inclusion checker for the #5518 T0 spike."""

import json


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def evaluate(spec, trace):
    """Check each visible output against the unique transition for state/input.

    Internal implementation events are deliberately ignored. An empty output
    list is missing evidence, never an implicit QUIESCENT output.
    """
    state = spec["initial"]
    transitions = spec["transitions"]
    seen_prefix = 0

    for index, exchange in enumerate(trace, start=1):
        stimulus = exchange["input"]
        matching = [
            item for item in transitions
            if item["from"] == state and _canonical(item["input"]) == _canonical(stimulus)
        ]
        if len(matching) != 1:
            return {
                "status": "NONCONFORMANT",
                "reason": "INPUT_NOT_SPECIFIED" if not matching else "AMBIGUOUS_SPEC_TRANSITION",
                "counterexample": {
                    "prefix_length": index,
                    "index": index,
                    "state": state,
                    "input": stimulus,
                    "observed_outputs": exchange.get("outputs", []),
                    "allowed_outputs": [],
                    "reason": "INPUT_NOT_SPECIFIED" if not matching else "AMBIGUOUS_SPEC_TRANSITION",
                },
            }

        transition = matching[0]
        outputs = exchange.get("outputs")
        if not isinstance(outputs, list):
            outputs = []
        if not outputs:
            return {
                "status": "UNKNOWN",
                "reason": "MISSING_OUTPUT_NOT_QUIESCENCE",
                "prefix_length": index,
                "state": state,
                "input": stimulus,
            }
        allowed = transition["allowed_outputs"]
        if len(outputs) != 1 or _canonical(outputs[0]) not in {_canonical(x) for x in allowed}:
            return {
                "status": "NONCONFORMANT",
                "reason": "OUTPUT_NOT_ALLOWED",
                "counterexample": {
                    "prefix_length": index,
                    "index": index,
                    "state": state,
                    "input": stimulus,
                    "observed_outputs": outputs,
                    "allowed_outputs": allowed,
                    "reason": "OUTPUT_NOT_ALLOWED",
                },
            }
        state = transition["to"]
        seen_prefix = index

    return {"status": "CONFORMANT", "reason": "ALL_PREFIXES_ALLOWED",
            "prefix_length": seen_prefix, "final_state": state}
