#!/usr/bin/env python3
"""Finite deterministic interface-refinement probe for Issue #5385 T1."""

from __future__ import annotations

import argparse
import itertools
import json
from collections import deque
from pathlib import Path


ALPHABET = (
    "invalidate",
    "trip",
    "start_comp",
    "refresh",
    "effect",
    "retry",
    "compensate",
)
DEPTH = 4
MANUAL_SUITE = (
    (),
    ("effect",),
    ("invalidate", "effect"),
    ("trip", "retry"),
    ("start_comp", "compensate"),
)
CANDIDATES = ("safe", "unsafe_output", "missing_refusal")


def spec_step(state: str, symbol: str) -> tuple[str, frozenset[str]]:
    """Independent specification transition used by the candidate runner."""
    if symbol == "invalidate":
        return ("stale" if state == "fresh" else state), frozenset({"OK"})
    if symbol == "trip":
        return "half_open", frozenset({"OK"})
    if symbol == "start_comp":
        return "comp_pending", frozenset({"OK"})
    if symbol == "refresh":
        return "fresh", frozenset({"OK"})
    if symbol == "effect":
        return state, frozenset({"GRANTED" if state == "fresh" else "REFUSED"})
    if symbol == "retry":
        return state, frozenset({"RETRY_ALLOWED" if state == "half_open" else "RETRY_DENIED"})
    if symbol == "compensate":
        return state, frozenset({"COMPENSATION_ALLOWED" if state == "comp_pending" else "COMPENSATION_DENIED"})
    raise ValueError(f"unknown input symbol: {symbol}")


def candidate_step(
    candidate: str, state: tuple[str, int], symbol: str
) -> tuple[tuple[str, int], frozenset[str]]:
    phase, stale_retry_streak = state
    next_phase = phase
    next_streak = stale_retry_streak

    if symbol == "invalidate":
        if phase == "fresh":
            next_phase, next_streak = "stale", 0
        outputs = frozenset({"OK"})
    elif symbol == "trip":
        next_phase, next_streak = "half_open", 0
        outputs = frozenset({"OK"})
    elif symbol == "start_comp":
        next_phase, next_streak = "comp_pending", 0
        outputs = frozenset({"OK"})
    elif symbol == "refresh":
        next_phase, next_streak = "fresh", 0
        outputs = frozenset({"OK"})
    elif symbol == "effect":
        if candidate == "unsafe_output" and phase == "stale" and stale_retry_streak >= 3:
            outputs = frozenset({"GRANTED"})
        else:
            outputs = frozenset({"GRANTED" if phase == "fresh" else "REFUSED"})
    elif symbol == "retry":
        if candidate == "missing_refusal" and phase == "stale" and stale_retry_streak >= 3:
            outputs = frozenset()
        else:
            outputs = frozenset({"RETRY_ALLOWED" if phase == "half_open" else "RETRY_DENIED"})
        if phase == "stale":
            next_streak = min(3, stale_retry_streak + 1)
    elif symbol == "compensate":
        outputs = frozenset({"COMPENSATION_ALLOWED" if phase == "comp_pending" else "COMPENSATION_DENIED"})
    else:
        raise ValueError(f"unknown input symbol: {symbol}")

    return (next_phase, next_streak), outputs


def run_word(candidate: str, word: tuple[str, ...]) -> list[list[str]]:
    state = ("fresh", 0)
    outputs: list[list[str]] = []
    for symbol in word:
        state, result = candidate_step(candidate, state, symbol)
        outputs.append(sorted(result))
    return outputs


def spec_word(word: tuple[str, ...]) -> list[list[str]]:
    state = "fresh"
    outputs: list[list[str]] = []
    for symbol in word:
        state, result = spec_step(state, symbol)
        outputs.append(sorted(result))
    return outputs


def all_bounded_words():
    yield ()
    for size in range(1, DEPTH + 1):
        yield from itertools.product(ALPHABET, repeat=size)


def alternating_refinement(candidate: str) -> dict:
    """Explore every environment input in the finite spec/implementation product.

    An implementation must define a transition for each environment input and
    every implementation output must be permitted by the specification.
    Refusal is an explicit output; an empty output set is not a refusal.
    """
    initial = ("fresh", ("fresh", 0))
    queue = deque([(initial, ())])
    visited = {initial}
    while queue:
        (spec_state, impl_state), prefix = queue.popleft()
        for symbol in ALPHABET:
            spec_next, permitted = spec_step(spec_state, symbol)
            impl_next, emitted = candidate_step(candidate, impl_state, symbol)
            word = prefix + (symbol,)
            if not emitted:
                return {
                    "status": "COUNTEREXAMPLE",
                    "counterexample_inputs": list(word),
                    "counterexample_kind": "MISSING_EXPLICIT_REFUSAL",
                    "explored_pair_states": len(visited),
                }
            if not emitted.issubset(permitted):
                return {
                    "status": "COUNTEREXAMPLE",
                    "counterexample_inputs": list(word),
                    "counterexample_kind": "OUTPUT_OUTSIDE_GUARANTEE",
                    "explored_pair_states": len(visited),
                }
            pair = (spec_next, impl_next)
            if pair not in visited:
                visited.add(pair)
                queue.append((pair, word))
    return {
        "status": "REFINES",
        "counterexample_inputs": None,
        "counterexample_kind": None,
        "explored_pair_states": len(visited),
    }


def build_records(source_commit: str, allocation_id: str):
    words = list(all_bounded_words())
    records = [
        {
            "kind": "header",
            "experiment": "issue-5385-t1-finite-alternating-refinement",
            "source_commit": source_commit,
            "allocation_id": allocation_id,
            "formal_invocations": 1,
            "input_alphabet": list(ALPHABET),
            "bounded_depth": DEPTH,
            "bounded_word_count": len(words),
            "manual_suite_word_count": len(MANUAL_SUITE),
            "finite_product_search": True,
            "candidate_count": len(CANDIDATES),
        }
    ]
    for candidate in CANDIDATES:
        for word in words:
            records.append(
                {
                    "kind": "trace",
                    "candidate": candidate,
                    "input": list(word),
                    "spec_outputs": spec_word(word),
                    "candidate_outputs": run_word(candidate, word),
                }
            )
        manual_equal = all(run_word(candidate, word) == spec_word(word) for word in MANUAL_SUITE)
        bounded_equal = all(run_word(candidate, word) == spec_word(word) for word in words)
        refinement = alternating_refinement(candidate)
        records.append(
            {
                "kind": "summary",
                "candidate": candidate,
                "manual_suite_equal": manual_equal,
                "bounded_depth": DEPTH,
                "bounded_word_count": len(words),
                "bounded_equivalent": bounded_equal,
                "refinement": refinement["status"],
                "counterexample_inputs": refinement["counterexample_inputs"],
                "counterexample_kind": refinement["counterexample_kind"],
                "explored_pair_states": refinement["explored_pair_states"],
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", default="CONSTRUCTION_UNFROZEN")
    parser.add_argument("--allocation-id", default="CONSTRUCTION_ONLY")
    args = parser.parse_args()
    records = build_records(args.source_commit, args.allocation_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    print(json.dumps({"records": len(records), "candidates": len(CANDIDATES), "bounded_words_per_candidate": 2801}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
