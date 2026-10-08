"""Exhaustively compare W2 close/terminal candidate and raw oracle intervals."""
import itertools
import json
from close_order_candidate import evaluate
from close_order_oracle import reconstruct


def intervals(limit):
    return [(lo, hi) for lo in range(limit + 1) for hi in range(lo, limit + 1)]


def event(kind, event_id, interval, lease="L", actuation="A"):
    time = ({"lower_ns": interval[0], "upper_ns": interval[1], "censoring": "bounded"}
            if interval is not None else {"lower_ns": None, "upper_ns": None, "censoring": "unknown"})
    lineage = {"lease_id": lease}
    if actuation is not None:
        lineage["actuation_id"] = actuation
    row = {"event_id": event_id, "event_type": kind, "time": time, "lineage": lineage}
    if kind == "INPUT_EDGE_BRACKET":
        row["payload"] = {"edge": "down", "transition_interval_ns": list(interval)}
    return row


def main():
    domain = intervals(5)
    edge_domain = domain
    close_domain = [None, *domain, "unknown", "invalid"]
    terminal_domain = [None, *domain, "unknown", "invalid"]
    lineages = [("L", "A"), ("L", "FOREIGN"), ("L", None), ("OTHER", "A")]
    checked = 0
    mismatch = None
    for edge_i, close_i, close_lineage, terminal_i in itertools.product(
            edge_domain, close_domain, lineages, terminal_domain):
        events = [event("LEASE_OPEN", "open", (0, 0))]
        if close_i is not None:
            interval = close_i if isinstance(close_i, tuple) else None
            if close_i == "invalid":
                close = event("LEASE_CLOSE", "close", (0, 0), *close_lineage)
                close["time"] = {"lower_ns": 4, "upper_ns": 2, "censoring": "bounded"}
            else:
                close = event("LEASE_CLOSE", "close", interval, *close_lineage)
            events.append(close)
        if terminal_i is not None:
            interval = terminal_i if isinstance(terminal_i, tuple) else None
            terminal = event("PROGRAM_TERMINAL", "terminal", interval)
            if terminal_i == "invalid":
                terminal["time"] = {"lower_ns": 4, "upper_ns": 2, "censoring": "bounded"}
            events.append(terminal)
        events.append(event("INPUT_EDGE_BRACKET", "edge", edge_i))
        cand, oracle = evaluate(events), reconstruct(events)
        checked += 1
        if cand != oracle:
            mismatch = {"events": events, "candidate": cand, "oracle": oracle}
            break
    result = {
        "schema": "w2-close-terminal-interval-exhaustive-v1",
        "disposition": "PASS_CANDIDATE_ORACLE_EQUIVALENCE_ONLY" if mismatch is None else "FAIL_CANDIDATE_ORACLE_MISMATCH",
        "edge_interval_domain": domain,
        "close_interval_domain": ["absent", *domain, "unknown", "invalid"],
        "terminal_interval_domain": ["absent", *domain, "unknown", "invalid"],
        "close_lineage_domain": [{"lease": l, "actuation": a} for l, a in lineages],
        "combinations_checked": checked,
        "mismatch": mismatch,
        "limits": ["Equivalence between separately implemented candidate and oracle, not proof against shared policy error.",
                   "Synthetic integer intervals only; no Docker, runtime or formal allocation."]
    }
    print(json.dumps(result, indent=2))
    if mismatch is not None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
