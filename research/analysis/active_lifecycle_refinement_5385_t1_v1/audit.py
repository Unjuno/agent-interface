#!/usr/bin/env python3
"""Raw-only checker; intentionally imports no candidate code."""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from collections import deque
from pathlib import Path


INPUTS = (
    "invalidate",
    "trip",
    "start_comp",
    "refresh",
    "effect",
    "retry",
    "compensate",
)
DEPTH_LIMIT = 4
MODEL_IDS = ("safe", "unsafe_output", "missing_refusal")
MANUAL_WORDS = (
    (),
    ("effect",),
    ("invalidate", "effect"),
    ("trip", "retry"),
    ("start_comp", "compensate"),
)


def words():
    yield ()
    for length in range(1, DEPTH_LIMIT + 1):
        yield from itertools.product(INPUTS, repeat=length)


def contract_transition(contract_state, action):
    # Separately authored transition table for the contract oracle.
    if action == "invalidate":
        return ("stale" if contract_state == "fresh" else contract_state), ("OK",)
    if action == "trip":
        return "half_open", ("OK",)
    if action == "start_comp":
        return "comp_pending", ("OK",)
    if action == "refresh":
        return "fresh", ("OK",)
    if action == "effect":
        return contract_state, (("GRANTED",) if contract_state == "fresh" else ("REFUSED",))
    if action == "retry":
        return contract_state, (("RETRY_ALLOWED",) if contract_state == "half_open" else ("RETRY_DENIED",))
    if action == "compensate":
        return contract_state, (("COMPENSATION_ALLOWED",) if contract_state == "comp_pending" else ("COMPENSATION_DENIED",))
    raise ValueError(action)


def implementation_transition(model, pair_state, action):
    phase, retries = pair_state
    target_phase, target_retries = phase, retries
    if action == "invalidate":
        if phase == "fresh":
            target_phase, target_retries = "stale", 0
        emitted = ("OK",)
    elif action == "trip":
        target_phase, target_retries = "half_open", 0
        emitted = ("OK",)
    elif action == "start_comp":
        target_phase, target_retries = "comp_pending", 0
        emitted = ("OK",)
    elif action == "refresh":
        target_phase, target_retries = "fresh", 0
        emitted = ("OK",)
    elif action == "effect":
        if model == "unsafe_output" and phase == "stale" and retries == 3:
            emitted = ("GRANTED",)
        else:
            emitted = (("GRANTED",) if phase == "fresh" else ("REFUSED",))
    elif action == "retry":
        if model == "missing_refusal" and phase == "stale" and retries == 3:
            emitted = ()
        else:
            emitted = (("RETRY_ALLOWED",) if phase == "half_open" else ("RETRY_DENIED",))
        if phase == "stale":
            target_retries = min(3, retries + 1)
    elif action == "compensate":
        emitted = (("COMPENSATION_ALLOWED",) if phase == "comp_pending" else ("COMPENSATION_DENIED",))
    else:
        raise ValueError(action)
    return (target_phase, target_retries), emitted


def output_word(model, word):
    state = ("fresh", 0)
    result = []
    for action in word:
        state, emitted = implementation_transition(model, state, action)
        result.append(sorted(emitted))
    return result


def contract_word(word):
    state = "fresh"
    result = []
    for action in word:
        state, emitted = contract_transition(state, action)
        result.append(sorted(emitted))
    return result


def refinement_oracle(model):
    """Finite input-universal/output-subset alternating simulation check."""
    start = ("fresh", ("fresh", 0))
    pending = deque([(start, ())])
    seen = {start}
    while pending:
        (contract_state, implementation_state), prefix = pending.popleft()
        for action in INPUTS:
            contract_next, permitted_tuple = contract_transition(contract_state, action)
            implementation_next, emitted_tuple = implementation_transition(model, implementation_state, action)
            context = prefix + (action,)
            permitted, emitted = set(permitted_tuple), set(emitted_tuple)
            if not emitted:
                return "COUNTEREXAMPLE", list(context), "MISSING_EXPLICIT_REFUSAL", len(seen)
            if emitted - permitted:
                return "COUNTEREXAMPLE", list(context), "OUTPUT_OUTSIDE_GUARANTEE", len(seen)
            successor = (contract_next, implementation_next)
            if successor not in seen:
                seen.add(successor)
                pending.append((successor, context))
    return "REFINES", None, None, len(seen)


def validate(records):
    errors = []
    headers = [record for record in records if record.get("kind") == "header"]
    summaries = [record for record in records if record.get("kind") == "summary"]
    traces = [record for record in records if record.get("kind") == "trace"]
    if len(headers) != 1:
        errors.append("header_count")
        header = {}
    else:
        header = headers[0]
    expected_words = list(words())
    expected_word_set = set(expected_words)
    if header.get("experiment") != "issue-5385-t1-finite-alternating-refinement":
        errors.append("experiment_identity")
    if header.get("input_alphabet") != list(INPUTS):
        errors.append("input_alphabet")
    if header.get("bounded_depth") != DEPTH_LIMIT:
        errors.append("bounded_depth")
    if header.get("bounded_word_count") != len(expected_words):
        errors.append("bounded_denominator")
    if header.get("formal_invocations") != 1:
        errors.append("formal_invocation_count")

    indexed = {}
    for row in traces:
        model = row.get("candidate")
        word = tuple(row.get("input", []))
        key = (model, word)
        if key in indexed:
            errors.append("duplicate_trace:" + repr(key))
        indexed[key] = row
    expected_keys = {(model, word) for model in MODEL_IDS for word in expected_word_set}
    if set(indexed) != expected_keys:
        errors.append("trace_domain_or_count")

    computed = {}
    for model in MODEL_IDS:
        for word in expected_words:
            row = indexed.get((model, word))
            if row is None:
                continue
            expected_contract = contract_word(word)
            expected_implementation = output_word(model, word)
            if row.get("spec_outputs") != expected_contract:
                errors.append("contract_trace_mismatch:" + model + repr(word))
            if row.get("candidate_outputs") != expected_implementation:
                errors.append("implementation_trace_mismatch:" + model + repr(word))
        manual_equal = all(output_word(model, word) == contract_word(word) for word in MANUAL_WORDS)
        bounded_equal = all(output_word(model, word) == contract_word(word) for word in expected_words)
        status, witness, kind, pair_states = refinement_oracle(model)
        computed[model] = {
            "manual_suite_equal": manual_equal,
            "bounded_depth": DEPTH_LIMIT,
            "bounded_word_count": len(expected_words),
            "bounded_equivalent": bounded_equal,
            "refinement": status,
            "counterexample_inputs": witness,
            "counterexample_kind": kind,
            "explored_pair_states": pair_states,
        }
    by_model = {}
    for summary in summaries:
        model = summary.get("candidate")
        if model in by_model:
            errors.append("duplicate_summary:" + str(model))
        by_model[model] = summary
    if set(by_model) != set(MODEL_IDS):
        errors.append("summary_domain_or_count")
    for model, expected in computed.items():
        summary = by_model.get(model)
        if summary is None:
            continue
        for field, expected_value in expected.items():
            if summary.get(field) != expected_value:
                errors.append("summary_mismatch:" + model + ":" + field)

    stats = {
        "candidate_count": len(MODEL_IDS),
        "bounded_words_per_candidate": len(expected_words),
        "trace_rows": len(traces),
        "summary_count": len(summaries),
    }
    return errors, stats


def mutation_controls(records):
    controls = {}
    changed = copy.deepcopy(records)
    row = next(
        record for record in changed
        if record.get("kind") == "trace"
        and record.get("candidate") == "safe"
        and record.get("input") == ["effect"]
    )
    row["candidate_outputs"] = [["REFUSED"]]
    controls["changed_trace_rejected"] = bool(validate(changed)[0])

    dropped = copy.deepcopy(records)
    dropped.remove(next(
        record for record in dropped
        if record.get("kind") == "trace"
        and record.get("candidate") == "safe"
        and record.get("input") == ["effect"]
    ))
    controls["dropped_trace_rejected"] = bool(validate(dropped)[0])

    wrong_witness = copy.deepcopy(records)
    summary = next(
        record for record in wrong_witness
        if record.get("kind") == "summary" and record.get("candidate") == "unsafe_output"
    )
    summary["counterexample_inputs"] = ["invalidate"]
    controls["wrong_counterexample_rejected"] = bool(validate(wrong_witness)[0])

    wrong_bound = copy.deepcopy(records)
    next(record for record in wrong_bound if record.get("kind") == "header")["bounded_depth"] = 5
    controls["wrong_bound_rejected"] = bool(validate(wrong_bound)[0])
    return controls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    digest = hashlib.sha256(args.raw.read_bytes()).hexdigest()
    try:
        records = [
            json.loads(line)
            for line in args.raw.read_text(encoding="utf-8").splitlines()
        ]
        errors, stats = validate(records)
        mutations = mutation_controls(records)
        if not all(mutations.values()):
            errors.append("mutation_control_not_rejected")
    except (OSError, ValueError, StopIteration) as exc:
        errors = ["raw_parse_or_validation_error:" + type(exc).__name__]
        stats = {"candidate_count": 0, "bounded_words_per_candidate": 2801, "trace_rows": 0, "summary_count": 0}
        mutations = {}
    result = {
        "status": "PASS_BOUNDED_ALTERNATING_REFINEMENT" if not errors else "FAIL_OR_STOP",
        "raw_sha256": digest,
        **stats,
        "errors": errors,
        "mutation_controls": mutations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_BOUNDED_ALTERNATING_REFINEMENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
