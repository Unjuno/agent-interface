#!/usr/bin/env python3
"""Finite partial-order replay experiment for Issue #4889 (stdlib only)."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path


EVENTS = ("OBS0", "OBS1", "PLAN0", "PLAN1", "TOOL0", "TOOL1", "OPEN", "CLOSE", "TICK", "REQUEST")
INITIAL = (-1, 0, -1, -1, -1, 0, 0, 0, 0)
# State fields: observation, observation revision, plan, plan revision,
# tool result, authority-open, authority generation, logical time, lease expiry.


def step(state, event):
    obs, obs_rev, plan, plan_rev, tool, auth, auth_gen, now, expiry = state
    out = "APPLIED"
    if event.startswith("OBS"):
        obs = int(event[-1])
        obs_rev = min(2, obs_rev + 1)
    elif event.startswith("PLAN"):
        plan = int(event[-1])
        plan_rev = obs_rev
        out = "BOUND_CURRENT" if obs >= 0 else "BOUND_WITHOUT_OBSERVATION"
    elif event.startswith("TOOL"):
        tool = int(event[-1])
    elif event == "OPEN":
        auth = 1
        auth_gen = min(2, auth_gen + 1)
        expiry = min(2, now + 1)
        out = "OPENED"
    elif event == "CLOSE":
        auth = 0
        auth_gen = min(2, auth_gen + 1)
        expiry = now
        out = "CLOSED"
    elif event == "TICK":
        now = min(2, now + 1)
        out = "TICKED"
    elif event == "REQUEST":
        if not auth:
            out = "REFUSED_CLOSED"
        elif now >= expiry:
            out = "REFUSED_EXPIRED"
        elif plan < 0 or plan_rev != obs_rev or plan != obs:
            out = "REFUSED_STALE_OR_MISSING_PLAN"
        elif tool != 1:
            out = "REFUSED_TOOL_RESULT"
        else:
            out = "ADMITTED"
    else:
        raise ValueError(event)
    return (obs, obs_rev, plan, plan_rev, tool, auth, auth_gen, now, expiry), out


def reachable_states():
    seen = {INITIAL}
    todo = [INITIAL]
    while todo:
        state = todo.pop()
        for event in EVENTS:
            nxt, _ = step(state, event)
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return sorted(seen)


def pair_independent(left, right, states):
    for state in states:
        after_l, out_l = step(state, left)
        after_lr, out_r_after_l = step(after_l, right)
        after_r, out_r = step(state, right)
        after_rl, out_l_after_r = step(after_r, left)
        if after_lr != after_rl or {"L": out_l, "R": out_r_after_l} != {"L": out_l_after_r, "R": out_r}:
            return False
    return True


def trace(state, events, order):
    outputs = {}
    for index in order:
        state, outputs[str(index)] = step(state, events[index])
    return state, outputs


def topo_orders(count, edges):
    predecessors = [0] * count
    for left, right in edges:
        predecessors[right] |= 1 << left
    full = (1 << count) - 1
    result = []

    def visit(mask, prefix):
        if mask == full:
            result.append(tuple(prefix))
            return
        for item in range(count):
            bit = 1 << item
            if not mask & bit and predecessors[item] & mask == predecessors[item]:
                visit(mask | bit, prefix + [item])

    visit(0, [])
    return result


def build_row(events, independent):
    n = len(events)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if not independent[events[i]][events[j]]]
    orders = topo_orders(n, edges)
    reference, ref_outputs = trace(INITIAL, events, tuple(range(n)))
    mismatches = 0
    first_mismatch = None
    for order in orders:
        final, outputs = trace(INITIAL, events, order)
        if final != reference or outputs != ref_outputs:
            mismatches += 1
            if first_mismatch is None:
                first_mismatch = list(order)
    return {
        "events": list(events),
        "dependent_edges": [list(edge) for edge in edges],
        "edge_count": len(edges),
        "total_order_edges": n * (n - 1) // 2,
        "linearizations": len(orders),
        "mismatches": mismatches,
        "first_mismatch": first_mismatch,
        "final_state": list(reference),
        "event_outputs": ref_outputs,
    }


def main():
    outdir = Path(os.environ.get("OUT", "/out"))
    outdir.mkdir(parents=True, exist_ok=False)
    states = reachable_states()
    independent = {a: {b: pair_independent(a, b, states) for b in EVENTS} for a in EVENTS}
    independence_rows = [{"left": a, "right": b, "independent": independent[a][b]} for a in EVENTS for b in EVENTS]
    raw_path = outdir / "RAW.jsonl"
    words = total_extensions = reduced_words = removed_edges = mismatch_words = 0
    with raw_path.open("w", encoding="utf-8", newline="\n") as raw:
        for length in range(5):
            for events in itertools.product(EVENTS, repeat=length):
                row = build_row(events, independent)
                raw.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
                words += 1
                total_extensions += row["linearizations"]
                reduced = row["edge_count"] < row["total_order_edges"]
                reduced_words += int(reduced)
                removed_edges += row["total_order_edges"] - row["edge_count"]
                mismatch_words += int(row["mismatches"] != 0)
    control = build_row(("OPEN", "CLOSE"), {a: {b: True for b in EVENTS} for a in EVENTS})
    # Explicitly omit OPEN-before-CLOSE: both orders must be considered and disagree.
    control_orders = topo_orders(2, [])
    control_reference, control_outputs = trace(INITIAL, ("OPEN", "CLOSE"), (0, 1))
    control_divergences = sum(
        trace(INITIAL, ("OPEN", "CLOSE"), order) != (control_reference, control_outputs)
        for order in control_orders
    )
    result = {
        "status": "PASS_PARTIAL_ORDER_REPLAY_SCOPED" if mismatch_words == 0 and reduced_words > 0 and control_divergences > 0 else "FAIL_OR_HOLD",
        "event_alphabet": list(EVENTS),
        "reachable_state_count": len(states),
        "pair_checks": len(EVENTS) ** 2 * len(states),
        "independent_pair_count": sum(sum(row.values()) for row in independent.values()),
        "event_words": words,
        "topological_linearizations": total_extensions,
        "words_with_strict_constraint_reduction": reduced_words,
        "ordering_constraints_removed": removed_edges,
        "words_with_mismatch": mismatch_words,
        "dependent_edge_omission_control_divergences": control_divergences,
        "formal_invocations": 1,
        "reruns": 0,
        "replacements": 0,
        "post_result_tuning": 0,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "independence_table": independence_rows,
    }
    (outdir / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (outdir / "NEGATIVE_CONTROL.json").write_text(json.dumps({
        "events": ["OPEN", "CLOSE"], "omitted_constraints": [[0, 1]],
        "linearizations": [list(x) for x in control_orders],
        "divergent_linearizations": control_divergences,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "independence_table"}, sort_keys=True))


if __name__ == "__main__":
    main()

