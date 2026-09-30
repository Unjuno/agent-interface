#!/usr/bin/env python3
"""Bounded active observation-table learner for a synthetic Mealy oracle."""

from __future__ import annotations

import itertools
import json
from pathlib import Path

ALPHABET = ("invalidate", "trip", "start_comp", "refresh", "effect", "retry", "compensate")
INITIAL = "fresh"
STATES = ("fresh", "stale", "half_open", "comp_pending")
MAX_EQ_DEPTH = 4
MAX_MEMBERSHIP = 500


def step(state: str, action: str) -> tuple[str, str]:
    if action == "invalidate":
        return ("stale" if state == "fresh" else state), "OK"
    if action == "trip":
        return "half_open", "OK"
    if action == "start_comp":
        return "comp_pending", "OK"
    if action == "refresh":
        return "fresh", "OK"
    if action == "effect":
        return state, "GRANTED" if state == "fresh" else "REFUSED"
    if action == "retry":
        return state, "RETRY_ALLOWED" if state == "half_open" else "RETRY_DENIED"
    if action == "compensate":
        return state, "COMPENSATION_ALLOWED" if state == "comp_pending" else "COMPENSATION_DENIED"
    raise ValueError(action)


def run_oracle(word: tuple[str, ...]) -> tuple[str, ...]:
    state = INITIAL
    outputs = []
    for action in word:
        state, output = step(state, action)
        outputs.append(output)
    return tuple(outputs)


def words_through(depth: int):
    yield ()
    for size in range(1, depth + 1):
        yield from itertools.product(ALPHABET, repeat=size)


class Learner:
    def __init__(self):
        self.membership_cache: dict[tuple[str, ...], tuple[str, ...]] = {}
        self.membership_calls = 0
        self.s = {()}
        self.e = {(a,) for a in ALPHABET} | {()}
        self.eq_rounds = []

    def membership(self, word):
        word = tuple(word)
        if word not in self.membership_cache:
            self.membership_calls += 1
            if self.membership_calls > MAX_MEMBERSHIP:
                raise RuntimeError("MEMBERSHIP_BUDGET_EXCEEDED")
            self.membership_cache[word] = run_oracle(word)
        return self.membership_cache[word]

    def row(self, prefix):
        prefix = tuple(prefix)
        base = self.membership(prefix)
        result = []
        for suffix in sorted(self.e):
            full = self.membership(prefix + suffix)
            result.append((suffix, full[len(prefix):]))
        return tuple(result)

    def close_and_consistent(self):
        while True:
            rows = {self.row(s) for s in self.s}
            unclosed = None
            for s in sorted(self.s):
                for a in ALPHABET:
                    candidate = s + (a,)
                    if self.row(candidate) not in rows:
                        unclosed = candidate
                        break
                if unclosed is not None:
                    break
            if unclosed is not None:
                self.s.add(unclosed)
                continue

            inconsistent = None
            ordered = sorted(self.s)
            for i, left in enumerate(ordered):
                for right in ordered[i + 1:]:
                    if self.row(left) != self.row(right):
                        continue
                    for action in ALPHABET:
                        left_row = self.row(left + (action,))
                        right_row = self.row(right + (action,))
                        if left_row != right_row:
                            for suffix in sorted(self.e):
                                if left_row[self._suffix_index(suffix)] != right_row[self._suffix_index(suffix)]:
                                    inconsistent = (action,) + suffix
                                    break
                            if inconsistent is not None:
                                break
                    if inconsistent is not None:
                        break
                if inconsistent is not None:
                    break
            if inconsistent is None:
                return
            self.e.add(inconsistent)

    def _suffix_index(self, suffix):
        return sorted(self.e).index(suffix)

    def hypothesis(self):
        self.close_and_consistent()
        representatives = {}
        for s in sorted(self.s):
            representatives.setdefault(self.row(s), s)
        row_to_state = {row: f"q{idx}" for idx, row in enumerate(representatives)}
        transitions = {}
        outputs = {}
        for row, representative in representatives.items():
            source = row_to_state[row]
            for action in ALPHABET:
                target_row = self.row(representative + (action,))
                if target_row not in row_to_state:
                    raise RuntimeError("TABLE_NOT_CLOSED")
                transitions[(source, action)] = row_to_state[target_row]
                outputs[(source, action)] = self.membership(representative + (action,))[-1]
        return row_to_state[self.row(())], transitions, outputs, representatives

    def predict(self, word, machine=None):
        if machine is None:
            machine = self.hypothesis()
        state, transitions, outputs, _ = machine
        result = []
        for action in word:
            result.append(outputs[(state, action)])
            state = transitions[(state, action)]
        return tuple(result)

    def learn(self):
        while True:
            machine = self.hypothesis()
            counterexample = None
            tested = 0
            for word in words_through(MAX_EQ_DEPTH):
                tested += 1
                if self.predict(word, machine) != run_oracle(word):
                    counterexample = word
                    break
            self.eq_rounds.append({
                "tested_prefix_words": tested,
                "counterexample": list(counterexample) if counterexample is not None else None,
            })
            if counterexample is None:
                return machine
            for end in range(len(counterexample) + 1):
                self.s.add(counterexample[:end])


def main():
    learner = Learner()
    machine = learner.learn()
    start, transitions, outputs, representatives = machine
    discovered = len(representatives)

    manual_suite = [
        ("effect",),
        ("invalidate", "effect"),
        ("refresh", "effect"),
        ("invalidate", "refresh", "effect"),
        ("trip", "refresh", "effect"),
    ]
    # Baseline distinguishes lifecycle classes only when its traces expose a
    # different immediate outcome for one of effect/retry/compensate.
    baseline_signatures = set()
    for word in manual_suite:
        baseline_signatures.add(run_oracle(word)[-1])

    out = Path("/out/formal.jsonl")
    records = [{
        "kind": "header",
        "allocation": "active-automata-5385-t0-orbstack-20260930-01",
        "alphabet": list(ALPHABET),
        "max_equivalence_depth": MAX_EQ_DEPTH,
        "equivalence_word_count": sum(len(ALPHABET) ** n for n in range(MAX_EQ_DEPTH + 1)),
        "membership_calls": learner.membership_calls,
        "membership_unique_words": len(learner.membership_cache),
        "hypothesis_state_count": discovered,
        "hypothesis_start": start,
        "representatives": {k: list(v) for k, v in ((str(i), s) for i, s in enumerate(representatives.values()))},
        "equivalence_rounds": learner.eq_rounds,
        "manual_suite": [list(w) for w in manual_suite],
        "manual_suite_identified_state_classes": len(baseline_signatures),
        "formal_invocations": 1,
    }]
    for word in words_through(MAX_EQ_DEPTH):
        records.append({
            "kind": "conformance",
            "input": list(word),
            "oracle_outputs": list(run_oracle(word)),
            "learned_outputs": list(learner.predict(word, machine)),
        })
    out.write_text("".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records), encoding="utf-8")
    print(json.dumps({
        "discovered_states": discovered,
        "membership_calls": learner.membership_calls,
        "equivalence_rounds": len(learner.eq_rounds),
        "equivalence_words": records[0]["equivalence_word_count"],
        "raw_records": len(records) - 1,
        "raw_path": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
