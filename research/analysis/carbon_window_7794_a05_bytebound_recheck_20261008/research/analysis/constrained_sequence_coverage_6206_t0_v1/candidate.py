"""Generate finite event-order suites for Issue #6206."""
from __future__ import annotations

import itertools
import json
import random
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
EVENTS = tuple(FIXTURE["events"])
MAX_LEN = FIXTURE["max_trace_length"]
RESET = dict(FIXTURE["reset"])
CANONICAL = tuple(FIXTURE["canonical_presence_order"])


def transition(state: dict, event: str, history: tuple[str, ...] = (), mutant: str | None = None) -> str:
    if event == "ACT":
        stale_permit = (
            mutant == "pair_stale_lease" and bool(history) and history[-1] == "REV"
        ) or (
            mutant == "triple_stale_permit" and len(history) >= 2 and history[-2:] == ("OBS", "REV")
        )
        if state["held"]:
            return "DENIED_HELD"
        if state["evidence_fresh"] and (state["lease_open"] or stale_permit):
            state["committed"] += 1
            state["held"] = True
            return "COMMITTED"
        if not state["lease_open"] and not stale_permit:
            return "DENIED_LEASE"
        return "DENIED_STALE"
    if event == "OBS":
        state["evidence_fresh"] = True
        return "OBSERVED"
    if event == "REV":
        was_held = state["held"]
        state["lease_open"] = False
        if was_held:
            state["held"] = False
            state["verified_releases"] += 1
        return "REVOKED_RELEASED" if was_held else "REVOKED_EMPTY"
    if event == "REL":
        if not state["held"]:
            raise ValueError("REL is infeasible without a live admitted hold")
        state["held"] = False
        state["verified_releases"] += 1
        return "RELEASED"
    if event == "STALE":
        was_held = state["held"]
        state["evidence_fresh"] = False
        if was_held:
            state["held"] = False
            state["verified_releases"] += 1
        return "STALE_RELEASED" if was_held else "STALE_EMPTY"
    if event == "PING":
        return "PING"
    raise ValueError(f"unknown event {event}")


def simulate(trace: tuple[str, ...], mutant: str | None = None) -> dict:
    state = dict(RESET)
    outputs = []
    history: tuple[str, ...] = ()
    for index, event in enumerate(trace):
        if event == "REL" and not state["held"]:
            return {"legal": False, "illegal_at": index}
        result = transition(state, event, history, mutant)
        outputs.append({"position": index, "event": event, "result": result})
        history += (event,)
    return {"legal": True, "outputs": outputs, "final_state": state}


def all_words(max_len: int = MAX_LEN) -> list[tuple[str, ...]]:
    return [word for size in range(max_len + 1) for word in itertools.product(EVENTS, repeat=size)]


def legal_words(max_len: int = MAX_LEN) -> list[tuple[str, ...]]:
    return [word for word in all_words(max_len) if simulate(word)["legal"]]


def presence_suite() -> list[tuple[str, ...]]:
    suite = []
    for mask in range(1 << len(CANONICAL)):
        trace = tuple(event for i, event in enumerate(CANONICAL) if mask & (1 << i))
        if simulate(trace)["legal"]:
            suite.append(trace)
    return suite


def feasible_adjacent_pairs(traces: list[tuple[str, ...]]) -> list[tuple[str, str]]:
    return sorted({(a, b) for trace in traces for a, b in zip(trace, trace[1:])})


def feasible_relative_pairs(traces: list[tuple[str, ...]]) -> list[tuple[str, str]]:
    pairs = set()
    for trace in traces:
        pairs.update((trace[i], trace[j]) for i in range(len(trace)) for j in range(i + 1, len(trace)))
    return sorted(pairs)


def feasible_relative_triples(traces: list[tuple[str, ...]]) -> list[tuple[str, str, str]]:
    triples = set()
    for trace in traces:
        triples.update((trace[i], trace[j], trace[k])
                       for i in range(len(trace))
                       for j in range(i + 1, len(trace))
                       for k in range(j + 1, len(trace)))
    return sorted(triples)


def ordered_pair_suite(traces: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    needed = feasible_adjacent_pairs(traces)
    sentinel = ("OBS", "REV", "ACT")
    chosen = set()
    for pair in needed:
        witnesses = [
            trace for trace in traces
            if any((a, b) == pair for a, b in zip(trace, trace[1:]))
            and not any(trace[i:i + 3] == sentinel for i in range(len(trace) - 2))
        ]
        if not witnesses:
            raise ValueError(f"no pair witness outside triple-control pattern: {pair}")
        chosen.add(min(witnesses, key=lambda item: (len(item), item)))
    return sorted(chosen, key=lambda item: (len(item), item))


def same_semantics(left: dict, right: dict) -> bool:
    if not left["legal"] or not right["legal"]:
        return left == right
    return left["final_state"] == right["final_state"] and [x["result"] for x in left["outputs"]] == [x["result"] for x in right["outputs"]]


def detects(suite: list[tuple[str, ...]], mutant: str) -> tuple[bool, list[str] | None]:
    for trace in suite:
        if not same_semantics(simulate(trace), simulate(trace, mutant)):
            return True, list(trace)
    return False, None


def pairwise_presence_coverage(suite: list[tuple[str, ...]]) -> dict:
    event_pairs = list(itertools.combinations(EVENTS, 2))
    universe = set()
    row_cover = []
    for trace in suite:
        present = set(trace)
        row_cover.append({(a, b, int(a in present), int(b in present)) for a, b in event_pairs})
    # The denominator is every presence-level tuple realizable by a legal canonical row.
    for cover in row_cover:
        universe.update(cover)
    covered = set().union(*row_cover) if row_cover else set()
    return {"feasible_tuple_count": len(universe), "covered_tuple_count": len(covered), "complete": universe == covered}


def main() -> None:
    start = time.perf_counter_ns()
    all_traces = all_words()
    legal = legal_words()
    static = presence_suite()
    pair_suite = ordered_pair_suite(legal)
    triple_suite = [word for word in all_words(3) if len(word) == 3 and simulate(word)["legal"]]
    rng = random.Random(FIXTURE["random_seed"])
    random_suite = [rng.choice(legal) for _ in pair_suite]

    adj_universe = feasible_adjacent_pairs(legal)
    rel_pair_universe = feasible_relative_pairs(legal)
    rel_triple_universe = feasible_relative_triples(legal)
    adj_covered = feasible_adjacent_pairs(pair_suite)
    rel_pair_covered = feasible_relative_pairs(pair_suite)
    rel_triple_covered = feasible_relative_triples(triple_suite)

    pair_static, pair_static_witness = detects(static, "pair_stale_lease")
    pair_ordered, pair_ordered_witness = detects(pair_suite, "pair_stale_lease")
    pair_random, pair_random_witness = detects(random_suite, "pair_stale_lease")
    triple_pair, triple_pair_witness = detects(pair_suite, "triple_stale_permit")
    triple_suite_hit, triple_suite_witness = detects(triple_suite, "triple_stale_permit")
    impossible = [["REL"], ["REV", "REL"]]
    impossible_rejected = all(not simulate(tuple(trace))["legal"] for trace in impossible)

    ping_ok = True
    for trace in legal:
        if "PING" not in trace:
            continue
        without_ping = tuple(event for event in trace if event != "PING")
        original = simulate(trace)
        reduced = simulate(without_ping)
        original_results = [row["result"] for row in original["outputs"] if row["event"] != "PING"]
        if original["final_state"] != reduced["final_state"] or original_results != [row["result"] for row in reduced["outputs"]]:
            ping_ok = False
            break

    result = {
        "schema": "constrained-sequence-coverage-candidate-v1",
        "allocation": "CONSTRAINED-ORDER-COVERAGE-6206-T0-20261002-01",
        "max_trace_length": MAX_LEN,
        "alphabet": list(EVENTS),
        "reset": RESET,
        "raw_word_count": len(all_traces),
        "exhaustive_legal_traces": [list(trace) for trace in legal],
        "suites": {
            "static_presence": [list(trace) for trace in static],
            "random_seed_6206": [list(trace) for trace in random_suite],
            "ordered_adjacent_pairs": [list(trace) for trace in pair_suite],
            "ordered_triples": [list(trace) for trace in triple_suite],
        },
        "coverage": {
            "feasible_adjacent_pairs": [list(x) for x in adj_universe],
            "ordered_pair_covered": [list(x) for x in adj_covered],
            "adjacent_complete": adj_universe == adj_covered,
            "feasible_relative_pairs": [list(x) for x in rel_pair_universe],
            "relative_pairs_covered_by_pair_suite": [list(x) for x in rel_pair_covered],
            "feasible_relative_triples": [list(x) for x in rel_triple_universe],
            "relative_triples_covered_by_triple_suite": [list(x) for x in rel_triple_covered],
            "static_presence_pairwise": pairwise_presence_coverage(static),
        },
        "fault_detection": {
            "pair_stale_lease": {
                "static_presence_detected": pair_static,
                "static_witness": pair_static_witness,
                "random_detected": pair_random,
                "random_witness": pair_random_witness,
                "ordered_pair_detected": pair_ordered,
                "ordered_pair_witness": pair_ordered_witness,
            },
            "triple_stale_permit": {
                "ordered_pair_detected": triple_pair,
                "ordered_pair_witness": triple_pair_witness,
                "ordered_triple_detected": triple_suite_hit,
                "ordered_triple_witness": triple_suite_witness,
            },
        },
        "controls": {
            "impossible_sequences": impossible,
            "impossible_sequences_rejected": impossible_rejected,
            "ping_order_invariant": ping_ok,
        },
        "counts": {
            "raw_words": len(all_traces),
            "legal_exhaustive": len(legal),
            "static_presence": len(static),
            "random_matched_budget": len(random_suite),
            "ordered_pair_suite": len(pair_suite),
            "ordered_triple_suite": len(triple_suite),
            "feasible_adjacent_pairs": len(adj_universe),
            "feasible_relative_pairs": len(rel_pair_universe),
            "feasible_relative_triples": len(rel_triple_universe),
        },
        "elapsed_ns": time.perf_counter_ns() - start,
    }
    (HERE / "candidate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"counts": result["counts"], "fault_detection": result["fault_detection"], "controls": result["controls"], "elapsed_ns": result["elapsed_ns"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
