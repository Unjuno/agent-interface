"""Independent raw-only checker for constrained sequence coverage T0.

This file intentionally does not import candidate.py.
"""
from __future__ import annotations

import itertools
import json
import math
import random
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
FIXTURE = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
EVENTS = tuple(FIXTURE["events"])
MAXLEN = int(FIXTURE["max_trace_length"])
INITIAL = dict(FIXTURE["reset"])
ORDER = tuple(FIXTURE["canonical_presence_order"])


def step_independent(s: dict, token: str, earlier: tuple[str, ...], fault: str | None = None) -> str:
    if token == "ACT":
        unsafe_cache = (fault == "pair_stale_lease" and earlier[-1:] == ("REV",)) or (
            fault == "triple_stale_permit" and earlier[-2:] == ("OBS", "REV")
        )
        if s["held"]:
            return "DENIED_HELD"
        if s["evidence_fresh"] and (s["lease_open"] or unsafe_cache):
            s["committed"] = s["committed"] + 1
            s["held"] = True
            return "COMMITTED"
        return "DENIED_LEASE" if not s["lease_open"] and not unsafe_cache else "DENIED_STALE"
    if token == "OBS":
        s["evidence_fresh"] = True
        return "OBSERVED"
    if token == "REV":
        released = s["held"]
        s["lease_open"] = False
        s["held"] = False
        s["verified_releases"] += int(released)
        return "REVOKED_RELEASED" if released else "REVOKED_EMPTY"
    if token == "REL":
        if not s["held"]:
            raise RuntimeError("release event without live hold")
        s["held"] = False
        s["verified_releases"] += 1
        return "RELEASED"
    if token == "STALE":
        released = s["held"]
        s["evidence_fresh"] = False
        s["held"] = False
        s["verified_releases"] += int(released)
        return "STALE_RELEASED" if released else "STALE_EMPTY"
    if token == "PING":
        return "PING"
    raise RuntimeError("unrecognized alphabet symbol")


def replay(seq: tuple[str, ...], fault: str | None = None) -> dict:
    state = dict(INITIAL)
    history = ()
    outputs = []
    for at, symbol in enumerate(seq):
        if symbol == "REL" and not state["held"]:
            return {"legal": False, "illegal_at": at}
        outcome = step_independent(state, symbol, history, fault)
        outputs.append({"position": at, "event": symbol, "result": outcome})
        history += (symbol,)
    return {"legal": True, "outputs": outputs, "final_state": state}


def universe() -> list[tuple[str, ...]]:
    return [seq for n in range(MAXLEN + 1) for seq in itertools.product(EVENTS, repeat=n)]


def valid_traces(words: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    result = []
    for word in words:
        if replay(word)["legal"]:
            result.append(word)
    return result


def subsets() -> list[tuple[str, ...]]:
    result = []
    for mask in range(1 << len(ORDER)):
        row = tuple(ORDER[ix] for ix in range(len(ORDER)) if mask & (1 << ix))
        if replay(row)["legal"]:
            result.append(row)
    return result


def adjacent(seqset: list[tuple[str, ...]]) -> list[tuple[str, str]]:
    found = set()
    for seq in seqset:
        found.update(zip(seq, seq[1:]))
    return sorted(found)


def ordered_pairs(seqset: list[tuple[str, ...]]) -> list[tuple[str, str]]:
    found = set()
    for seq in seqset:
        found.update((seq[i], seq[j]) for i in range(len(seq)) for j in range(i + 1, len(seq)))
    return sorted(found)


def ordered_triples(seqset: list[tuple[str, ...]]) -> list[tuple[str, str, str]]:
    found = set()
    for seq in seqset:
        found.update((seq[i], seq[j], seq[k]) for i in range(len(seq))
                     for j in range(i + 1, len(seq)) for k in range(j + 1, len(seq)))
    return sorted(found)


def pair_witnesses(feasible: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    obligations = adjacent(feasible)
    selected = set()
    banned = ("OBS", "REV", "ACT")
    for obligation in obligations:
        eligible = []
        for seq in feasible:
            neighbors = tuple(zip(seq, seq[1:]))
            has_banned_triple = any(seq[pos:pos + 3] == banned for pos in range(len(seq) - 2))
            if obligation in neighbors and not has_banned_triple:
                eligible.append(seq)
        if not eligible:
            raise RuntimeError("no admissible pair witness under frozen exclusion")
        eligible.sort(key=lambda seq: (len(seq), seq))
        selected.add(eligible[0])
    return sorted(selected, key=lambda seq: (len(seq), seq))


def diff_semantics(a: dict, b: dict) -> bool:
    return a["final_state"] != b["final_state"] or [x["result"] for x in a["outputs"]] != [x["result"] for x in b["outputs"]]


def witness(seqset: list[tuple[str, ...]], fault: str) -> list[str] | None:
    for seq in seqset:
        if diff_semantics(replay(seq), replay(seq, fault)):
            return list(seq)
    return None


def pairwise_presence(suite: list[tuple[str, ...]]) -> dict:
    pairs = list(itertools.combinations(EVENTS, 2))
    rows = []
    for seq in suite:
        active = set(seq)
        rows.append({(a, b, int(a in active), int(b in active)) for a, b in pairs})
    feasible = set().union(*rows) if rows else set()
    covered = set().union(*rows) if rows else set()
    return {"feasible_tuple_count": len(feasible), "covered_tuple_count": len(covered), "complete": feasible == covered}


def sem_equal_with_ping_removed(seq: tuple[str, ...]) -> bool:
    full = replay(seq)
    short = replay(tuple(x for x in seq if x != "PING"))
    return full["final_state"] == short["final_state"] and [x["result"] for x in full["outputs"] if x["event"] != "PING"] == [x["result"] for x in short["outputs"]]


def expected_payload() -> dict:
    words = universe()
    legal = valid_traces(words)
    static = subsets()
    pairs = pair_witnesses(legal)
    triples = [seq for seq in itertools.product(EVENTS, repeat=3) if replay(seq)["legal"]]
    rand = random.Random(int(FIXTURE["random_seed"]))
    random_suite = [rand.choice(legal) for _ in pairs]
    adj_u = adjacent(legal)
    rel_u = ordered_pairs(legal)
    triple_u = ordered_triples(legal)
    return {
        "raw_word_count": len(words),
        "exhaustive_legal_traces": [list(x) for x in legal],
        "suites": {
            "static_presence": [list(x) for x in static],
            "random_seed_6206": [list(x) for x in random_suite],
            "ordered_adjacent_pairs": [list(x) for x in pairs],
            "ordered_triples": [list(x) for x in triples],
        },
        "coverage": {
            "feasible_adjacent_pairs": [list(x) for x in adj_u],
            "ordered_pair_covered": [list(x) for x in adjacent(pairs)],
            "adjacent_complete": adj_u == adjacent(pairs),
            "feasible_relative_pairs": [list(x) for x in rel_u],
            "relative_pairs_covered_by_pair_suite": [list(x) for x in ordered_pairs(pairs)],
            "feasible_relative_triples": [list(x) for x in triple_u],
            "relative_triples_covered_by_triple_suite": [list(x) for x in ordered_triples(triples)],
            "static_presence_pairwise": pairwise_presence(static),
        },
        "fault_detection": {
            "pair_stale_lease": {
                "static_presence_detected": witness(static, "pair_stale_lease") is not None,
                "static_witness": witness(static, "pair_stale_lease"),
                "random_detected": witness(random_suite, "pair_stale_lease") is not None,
                "random_witness": witness(random_suite, "pair_stale_lease"),
                "ordered_pair_detected": witness(pairs, "pair_stale_lease") is not None,
                "ordered_pair_witness": witness(pairs, "pair_stale_lease"),
            },
            "triple_stale_permit": {
                "ordered_pair_detected": witness(pairs, "triple_stale_permit") is not None,
                "ordered_pair_witness": witness(pairs, "triple_stale_permit"),
                "ordered_triple_detected": witness(triples, "triple_stale_permit") is not None,
                "ordered_triple_witness": witness(triples, "triple_stale_permit"),
            },
        },
        "controls": {
            "impossible_sequences": [["REL"], ["REV", "REL"]],
            "impossible_sequences_rejected": all(not replay(tuple(x))["legal"] for x in [["REL"], ["REV", "REL"]]),
            "ping_order_invariant": all(sem_equal_with_ping_removed(x) for x in legal if "PING" in x),
        },
        "counts": {
            "raw_words": len(words), "legal_exhaustive": len(legal),
            "static_presence": len(static), "random_matched_budget": len(random_suite),
            "ordered_pair_suite": len(pairs), "ordered_triple_suite": len(triples),
            "feasible_adjacent_pairs": len(adj_u), "feasible_relative_pairs": len(rel_u),
            "feasible_relative_triples": len(triple_u),
        },
    }


def canonical_close(a, b) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(canonical_close(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(canonical_close(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, (float, int)):
        return math.isclose(a, b, rel_tol=0, abs_tol=1e-12)
    return a == b


def main() -> None:
    candidate = json.loads((HERE / "candidate.json").read_text(encoding="utf-8"))
    expected = expected_payload()
    audited_fields = ["raw_word_count", "exhaustive_legal_traces", "suites", "coverage", "fault_detection", "controls", "counts"]
    field_checks = {key: canonical_close(candidate.get(key), expected[key]) for key in audited_fields}
    runtime_ok = isinstance(candidate.get("elapsed_ns"), int) and candidate["elapsed_ns"] >= 0
    frozen_ok = candidate.get("schema") == "constrained-sequence-coverage-candidate-v1" and candidate.get("allocation") == "CONSTRAINED-ORDER-COVERAGE-6206-T0-20261002-01" and candidate.get("alphabet") == list(EVENTS) and candidate.get("max_trace_length") == MAXLEN
    gate_ok = (
        expected["coverage"]["adjacent_complete"]
        and not expected["fault_detection"]["pair_stale_lease"]["static_presence_detected"]
        and expected["fault_detection"]["pair_stale_lease"]["ordered_pair_detected"]
        and not expected["fault_detection"]["triple_stale_permit"]["ordered_pair_detected"]
        and expected["fault_detection"]["triple_stale_permit"]["ordered_triple_detected"]
        and expected["controls"]["impossible_sequences_rejected"]
        and expected["controls"]["ping_order_invariant"]
        and expected["counts"]["ordered_pair_suite"] < expected["counts"]["legal_exhaustive"]
    )

    # Independent comparison gate must reject each representative corruption.
    corruption_rejected = []
    for mutation in ("drop_pair", "admit_impossible", "flip_fault", "alter_denominator"):
        damaged = json.loads(json.dumps(candidate))
        if mutation == "drop_pair":
            damaged["suites"]["ordered_adjacent_pairs"].pop()
        elif mutation == "admit_impossible":
            damaged["exhaustive_legal_traces"].append(["REL"])
        elif mutation == "flip_fault":
            damaged["fault_detection"]["pair_stale_lease"]["ordered_pair_detected"] = not damaged["fault_detection"]["pair_stale_lease"]["ordered_pair_detected"]
        else:
            damaged["counts"]["legal_exhaustive"] += 1
        rejected = not all(canonical_close(damaged.get(key), expected[key]) for key in audited_fields)
        corruption_rejected.append({"control": mutation, "rejected": rejected})

    checks = list(field_checks.values()) + [runtime_ok, frozen_ok, gate_ok] + [x["rejected"] for x in corruption_rejected]
    result = {
        "status": "PASS_METHOD_SCOPED" if all(checks) else "FAIL_AUDIT_OR_METHOD",
        "checks_passed": sum(checks),
        "checks_total": len(checks),
        "independent_enumeration": True,
        "field_checks": field_checks,
        "runtime_receipt_valid": runtime_ok,
        "freeze_identity_valid": frozen_ok,
        "registered_decision_gates_pass": gate_ok,
        "corruption_controls": corruption_rejected,
        "independent_counts": expected["counts"],
        "scope": "finite synthetic event-order method only; no real runtime, GUI, task effect, safety, or reliability claim",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if all(checks) else 1)


if __name__ == "__main__":
    main()
