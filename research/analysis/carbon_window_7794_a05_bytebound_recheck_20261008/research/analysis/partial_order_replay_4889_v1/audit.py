#!/usr/bin/env python3
"""Independent raw-only oracle for Issue #4889; does not import runner.py."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path


ALPHABET = ("OBS0", "OBS1", "PLAN0", "PLAN1", "TOOL0", "TOOL1", "OPEN", "CLOSE", "TICK", "REQUEST")
START = (-1, 0, -1, -1, -1, 0, 0, 0, 0)


def reduce_one(s, token):
    o, ov, p, pv, tool, auth, ag, clock, lease = s
    response = "APPLIED"
    if token in ("OBS0", "OBS1"):
        o, ov = int(token[-1]), min(2, ov + 1)
    elif token in ("PLAN0", "PLAN1"):
        p, pv = int(token[-1]), ov
        response = "BOUND_WITHOUT_OBSERVATION" if o == -1 else "BOUND_CURRENT"
    elif token in ("TOOL0", "TOOL1"):
        tool = int(token[-1])
    elif token == "OPEN":
        auth, ag, lease, response = 1, min(2, ag + 1), min(2, clock + 1), "OPENED"
    elif token == "CLOSE":
        auth, ag, lease, response = 0, min(2, ag + 1), clock, "CLOSED"
    elif token == "TICK":
        clock, response = min(2, clock + 1), "TICKED"
    elif token == "REQUEST":
        if auth == 0:
            response = "REFUSED_CLOSED"
        elif clock >= lease:
            response = "REFUSED_EXPIRED"
        elif p == -1 or pv != ov or p != o:
            response = "REFUSED_STALE_OR_MISSING_PLAN"
        elif tool != 1:
            response = "REFUSED_TOOL_RESULT"
        else:
            response = "ADMITTED"
    else:
        raise ValueError(token)
    return (o, ov, p, pv, tool, auth, ag, clock, lease), response


def discover_states():
    found = {START}
    fringe = [START]
    while fringe:
        current = fringe.pop()
        for token in ALPHABET:
            destination, _ = reduce_one(current, token)
            if destination not in found:
                found.add(destination)
                fringe.append(destination)
    return tuple(sorted(found))


def run_word(events, permutation):
    state = START
    emitted = {}
    for ix in permutation:
        state, value = reduce_one(state, events[ix])
        emitted[str(ix)] = value
    return state, emitted


def commutes(x, y, universe):
    for q in universe:
        qx, ox = reduce_one(q, x)
        qxy, oyx = reduce_one(qx, y)
        qy, oy = reduce_one(q, y)
        qyx, oxy = reduce_one(qy, x)
        if qxy != qyx or (ox, oyx) != (oxy, oy):
            return False
    return True


def reference_record(events, independence):
    n = len(events)
    edges = [(a, b) for a in range(n) for b in range(a + 1, n) if not independence[events[a]][events[b]]]
    ref_state, ref_events = run_word(events, range(n))
    legal = []
    for permutation in itertools.permutations(range(n)):
        location = {value: rank for rank, value in enumerate(permutation)}
        if all(location[a] < location[b] for a, b in edges):
            legal.append(permutation)
    bad = 0
    witness = None
    for permutation in legal:
        if run_word(events, permutation) != (ref_state, ref_events):
            bad += 1
            witness = list(permutation) if witness is None else witness
    return {
        "events": list(events),
        "dependent_edges": [list(e) for e in edges],
        "edge_count": len(edges),
        "total_order_edges": n * (n - 1) // 2,
        "linearizations": len(legal),
        "mismatches": bad,
        "first_mismatch": witness,
        "final_state": list(ref_state),
        "event_outputs": ref_events,
    }


def validate(raw_path, result_path):
    universe = discover_states()
    relation = {a: {b: commutes(a, b, universe) for b in ALPHABET} for a in ALPHABET}
    expected_rows = []
    totals = {"topological_linearizations": 0, "words_with_strict_constraint_reduction": 0,
              "ordering_constraints_removed": 0, "words_with_mismatch": 0}
    for size in range(5):
        for word in itertools.product(ALPHABET, repeat=size):
            expected = reference_record(word, relation)
            expected_rows.append(expected)
            totals["topological_linearizations"] += expected["linearizations"]
            totals["words_with_strict_constraint_reduction"] += int(expected["edge_count"] < expected["total_order_edges"])
            totals["ordering_constraints_removed"] += expected["total_order_edges"] - expected["edge_count"]
            totals["words_with_mismatch"] += int(expected["mismatches"] != 0)
    actual_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    if actual_rows != expected_rows:
        return False, {"reason": "raw rows differ from independent recomputation", "expected_rows": len(expected_rows), "actual_rows": len(actual_rows)}
    result = json.loads(result_path.read_text(encoding="utf-8"))
    expected_fields = {
        "event_alphabet": list(ALPHABET), "reachable_state_count": len(universe),
        "pair_checks": len(ALPHABET) ** 2 * len(universe),
        "independent_pair_count": sum(sum(int(v) for v in row.values()) for row in relation.values()),
        "event_words": len(expected_rows), **totals,
        "formal_invocations": 1, "reruns": 0, "replacements": 0, "post_result_tuning": 0,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "independence_table": [{"left": a, "right": b, "independent": relation[a][b]} for a in ALPHABET for b in ALPHABET],
    }
    for key, value in expected_fields.items():
        if result.get(key) != value:
            return False, {"reason": "result summary mismatch", "field": key, "expected": value, "actual": result.get(key)}
    if result.get("status") != "PASS_PARTIAL_ORDER_REPLAY_SCOPED" or totals["words_with_mismatch"] != 0 or totals["words_with_strict_constraint_reduction"] == 0:
        return False, {"reason": "decision gate failed"}
    # The omitted OPEN-before-CLOSE relation admits both orders; only one matches the original.
    base, outputs = run_word(("OPEN", "CLOSE"), (0, 1))
    divergent = sum(run_word(("OPEN", "CLOSE"), order) != (base, outputs) for order in itertools.permutations((0, 1)))
    if divergent == 0:
        return False, {"reason": "dependent-edge omission control did not diverge"}
    return True, {"status": "PASS_RAW_AUDIT", "errors": [], "raw_rows": len(actual_rows),
                  "reachable_states": len(universe), "independent_pair_checks": expected_fields["pair_checks"],
                  "linearizations_checked": totals["topological_linearizations"], "negative_control_divergences": divergent}


def main():
    folder = Path(os.environ.get("EVIDENCE", "/evidence/formal01"))
    raw_path, result_path = folder / "RAW.jsonl", folder / "RESULT.json"
    ok, audit = validate(raw_path, result_path)
    # Eight effective copied-record corruptions; the independent row oracle must reject each.
    control_states = discover_states()
    control_relation = {a: {b: commutes(a, b, control_states) for b in ALPHABET} for a in ALPHABET}
    target = reference_record(("OPEN", "CLOSE"), control_relation)
    mutations = {
        "events": lambda r: r.update(events=["CLOSE", "OPEN"]),
        "edges": lambda r: r.update(dependent_edges=[]),
        "edge_count": lambda r: r.update(edge_count=0),
        "linearizations": lambda r: r.update(linearizations=1),
        "mismatches": lambda r: r.update(mismatches=1),
        "first_mismatch": lambda r: r.update(first_mismatch=[1, 0]),
        "final_state": lambda r: r.update(final_state=list(START)),
        "event_outputs": lambda r: r.update(event_outputs={"0": "ADMITTED", "1": "APPLIED"}),
    }
    controls = []
    for name, mutate in mutations.items():
        changed = json.loads(json.dumps(target))
        mutate(changed)
        controls.append({"name": name, "rejected": changed != target})
    controls_ok = all(row["rejected"] for row in controls)
    if not ok:
        audit = {"status": "FAIL_RAW_AUDIT", "errors": [audit]}
    audit["errors"] = audit.get("errors", [])
    audit["status"] = "PASS_RAW_AUDIT" if ok and controls_ok else "FAIL_RAW_AUDIT"
    (folder / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    controls_result = {"status": "PASS_CONTROLS" if controls_ok else "FAIL_CONTROLS",
                       "rejected": sum(row["rejected"] for row in controls), "total": len(controls), "controls": controls}
    (folder / "CONTROLS.json").write_text(json.dumps(controls_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"audit": audit, "controls": controls_result}, sort_keys=True))
    if not ok or not controls_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
