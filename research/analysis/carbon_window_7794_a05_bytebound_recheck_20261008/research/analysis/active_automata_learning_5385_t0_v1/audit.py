#!/usr/bin/env python3
"""Independent raw-only audit; intentionally does not import experiment.py."""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

SYMBOLS = ("invalidate", "trip", "start_comp", "refresh", "effect", "retry", "compensate")
LIMIT = 4


def reference(word):
    state = "fresh"
    outputs = []
    for symbol in word:
        if symbol == "invalidate":
            if state == "fresh":
                state = "stale"
            output = "OK"
        elif symbol == "trip":
            state, output = "half_open", "OK"
        elif symbol == "start_comp":
            state, output = "comp_pending", "OK"
        elif symbol == "refresh":
            state, output = "fresh", "OK"
        elif symbol == "effect":
            output = "GRANTED" if state == "fresh" else "REFUSED"
        elif symbol == "retry":
            output = "RETRY_ALLOWED" if state == "half_open" else "RETRY_DENIED"
        elif symbol == "compensate":
            output = "COMPENSATION_ALLOWED" if state == "comp_pending" else "COMPENSATION_DENIED"
        else:
            raise ValueError(symbol)
        outputs.append(output)
    return outputs


def validate(records):
    headers = [r for r in records if r.get("kind") == "header"]
    rows = [r for r in records if r.get("kind") == "conformance"]
    errors = []
    if len(headers) != 1:
        errors.append("header_count")
        header = {}
    else:
        header = headers[0]
    expected_words = list(words())
    if [tuple(r.get("input", [])) for r in rows] != expected_words:
        errors.append("language_coverage_or_order")
    for row in rows:
        word = tuple(row.get("input", []))
        expected = reference(word)
        if row.get("oracle_outputs") != expected:
            errors.append("oracle_output_mismatch:" + repr(word))
        if row.get("learned_outputs") != expected:
            errors.append("learned_counterexample:" + repr(word))
        # Check authority against independently reconstructed hidden state.
        state = "fresh"
        for symbol, output in zip(word, expected):
            if output == "GRANTED" and state != "fresh":
                errors.append("unsafe_grant:" + repr(word))
            if symbol == "invalidate" and state == "fresh":
                state = "stale"
            elif symbol == "trip":
                state = "half_open"
            elif symbol == "start_comp":
                state = "comp_pending"
            elif symbol == "refresh":
                state = "fresh"
    if header.get("equivalence_word_count") != len(expected_words):
        errors.append("equivalence_denominator")
    if header.get("membership_calls", 10**9) > 500:
        errors.append("membership_budget")
    if header.get("hypothesis_state_count") != 4:
        errors.append("state_count")
    if header.get("manual_suite_identified_state_classes", 10**9) >= 4:
        errors.append("manual_baseline_not_weaker")
    if header.get("formal_invocations") != 1:
        errors.append("invocation_count")
    return errors, rows, header


def words():
    yield ()
    for length in range(1, LIMIT + 1):
        yield from itertools.product(SYMBOLS, repeat=length)


def audit(raw_path: Path):
    digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    records = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    errors, rows, header = validate(records)
    # Mutate independent copies; each corruption must be rejected.
    changed = json.loads(json.dumps(records))
    next(r for r in changed if r.get("kind") == "conformance" and r.get("input") == ["effect"])["learned_outputs"] = ["REFUSED"]
    mutation_output_rejected = bool(validate(changed)[0])
    dropped = [r for r in records if not (r.get("kind") == "conformance" and r.get("input") == ["effect"])]
    mutation_drop_rejected = bool(validate(dropped)[0])
    wrong_states = json.loads(json.dumps(records))
    next(r for r in wrong_states if r.get("kind") == "header")["hypothesis_state_count"] = 3
    mutation_state_rejected = bool(validate(wrong_states)[0])
    over_budget = json.loads(json.dumps(records))
    next(r for r in over_budget if r.get("kind") == "header")["membership_calls"] = 501
    mutation_budget_rejected = bool(validate(over_budget)[0])
    if not all((mutation_output_rejected, mutation_drop_rejected, mutation_state_rejected, mutation_budget_rejected)):
        errors.append("mutation_control_not_rejected")
    audit_result = {
        "status": "PASS_ACTIVE_LEARNING_SCOPED" if not errors else "FAIL_OR_STOP",
        "raw_sha256": digest,
        "rows": len(rows),
        "expected_bounded_words": sum(len(SYMBOLS) ** n for n in range(LIMIT + 1)),
        "membership_calls": header.get("membership_calls"),
        "hypothesis_state_count": header.get("hypothesis_state_count"),
        "errors": errors,
        "mutation_controls": {
            "changed_output_rejected": mutation_output_rejected,
            "dropped_word_rejected": mutation_drop_rejected,
            "wrong_state_count_rejected": mutation_state_rejected,
            "budget_overrun_rejected": mutation_budget_rejected,
        },
    }
    return audit_result


def main():
    raw = Path("/out/formal.jsonl")
    result = audit(raw)
    Path("/out/audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_ACTIVE_LEARNING_SCOPED" else 1)


if __name__ == "__main__":
    main()
