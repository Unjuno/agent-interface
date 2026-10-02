"""Finite contract-bound audit: lease close bounds authority; terminal is independent."""
import itertools
import json
from lease_authority_candidate_v3 import decide
from lease_authority_oracle_v3 import reconstruct


def intervals(limit=5):
    return [(lo, hi) for lo in range(limit + 1) for hi in range(lo, limit + 1)]


def timed(kind, event_id, bounds, lease="L", actuation="A"):
    lineage = {"lease_id": lease, "parent_event_ids": []}
    if actuation is not None:
        lineage["actuation_id"] = actuation
    if bounds == "unknown":
        stamp = {"lower_ns": None, "upper_ns": None, "censoring": "unknown"}
    elif bounds == "invalid":
        stamp = {"lower_ns": 4, "upper_ns": 2, "censoring": "bounded"}
    else:
        stamp = {"lower_ns": bounds[0], "upper_ns": bounds[1], "censoring": "bounded"}
    return {"event_id": event_id, "event_type": kind, "time": stamp,
            "lineage": lineage, "payload": {}}


def expected(edge, close, lineage):
    if close is None:
        return "AUTHORIZED_MATCH"
    if lineage[0] != "L":
        return "AUTHORIZED_MATCH"
    if lineage != ("L", "A"):
        return "HOLD_CLOSE_LINEAGE_UNRESOLVED"
    if close in ("unknown", "invalid"):
        return "HOLD_UNKNOWN_CLOSE_TIME"
    if close[1] < edge[0]:
        return "REJECT_EDGE_AFTER_LEASE_CLOSE"
    if edge[1] >= close[0]:
        return "HOLD_EDGE_CLOSE_ORDER_UNCERTAIN"
    return "AUTHORIZED_MATCH"


def main():
    domain = intervals()
    close_domain = [None, *domain, "unknown", "invalid"]
    lineages = [("L", "A"), ("L", "FOREIGN"), ("L", None), ("OTHER", "A")]
    terminals = [None, *domain, "unknown", "invalid"]
    checked, mismatch, expected_mismatch = 0, None, None
    for edge, closure, lineage, terminal in itertools.product(domain, close_domain, lineages, terminals):
        rows = [timed("LEASE_OPEN", "open", (0, 0))]
        if closure is not None:
            rows.append(timed("LEASE_CLOSE", "close", closure, *lineage))
        if terminal is not None:
            rows.append(timed("PROGRAM_TERMINAL", "terminal", terminal))
        rows.append({"event_id": "edge", "event_type": "INPUT_EDGE_BRACKET",
                     "time": {"lower_ns": edge[0], "upper_ns": edge[1], "censoring": "bounded"},
                     "lineage": {"lease_id": "L", "actuation_id": "A"},
                     "payload": {"transition_interval_ns": list(edge)}})
        candidate, oracle = decide(rows), reconstruct(rows)
        checked += 1
        if candidate != oracle:
            mismatch = {"candidate": candidate, "oracle": oracle, "rows": rows}
            break
        wanted = expected(edge, closure, lineage)
        actual = candidate[0]["status"]
        if actual != wanted:
            expected_mismatch = {"expected_from_lease_interval_contract": wanted,
                                 "actual": actual, "edge": edge, "close": closure,
                                 "lineage": lineage, "terminal": terminal}
            break
    result = {
        "schema": "w2-lease-authority-finite-audit-v3",
        "disposition": "PASS_FINITE_LEASE_AUTHORITY_POLICY_ONLY" if mismatch is None and expected_mismatch is None else "FAIL_FINITE_AUDIT",
        "domain_size": {"edge_intervals": len(domain), "close_intervals": len(close_domain),
                        "close_lineages": len(lineages), "terminal_intervals": len(terminals)},
        "combinations_checked": checked,
        "candidate_oracle_mismatch": mismatch,
        "lease_contract_rule_mismatch": expected_mismatch,
        "limits": ["Bounded synthetic integer intervals only.",
                   "Finite policy audit does not establish live authority, backend timing or product safety.",
                   "Lease closure is treated as the authority boundary; PROGRAM_TERMINAL is not promoted to LEASE_CLOSE."]
    }
    print(json.dumps(result, indent=2))
    if mismatch is not None or expected_mismatch is not None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
