#!/usr/bin/env python3
"""Independent raw-trace audit for the bounded Issue #5410 simulator."""
import json
import sys

SCENARIOS = (
    "opposed_order_deadlock", "lease_expiry_recovery", "cancellation_release",
    "authority_revocation_release", "hidden_dependency", "retry_backoff",
    "independent_workflows",
)
POLICIES = ("NAIVE", "GLOBAL_EXCLUSIVE", "SCC_GUARD", "SAFE_REACHABILITY")
RESOURCES = set("ABCDE")


def main(path):
    report = json.loads(open(path, encoding="utf-8").read())
    errors = []
    rows = report.get("runs", [])
    if report.get("resources") != sorted(RESOURCES) or report.get("capacity_per_resource") != 1:
        errors.append("resource model mismatch")
    if report.get("policies") != list(POLICIES) or report.get("scenario_count") != len(SCENARIOS):
        errors.append("policy/scenario declaration mismatch")
    expected_pairs = {(s, p) for s in SCENARIOS for p in POLICIES}
    actual_pairs = {(row.get("scenario"), row.get("policy")) for row in rows}
    if actual_pairs != expected_pairs or len(rows) != len(expected_pairs):
        errors.append("run coverage mismatch")

    for row in rows:
        owner = {}
        completed = set()
        released = set()
        prior_tick = -1
        for event in row.get("trace", []):
            tick = event.get("tick", -1)
            if tick < prior_tick:
                errors.append(f"{row.get('scenario')}/{row.get('policy')}: trace time regressed")
            prior_tick = tick
            name = event.get("workflow")
            kind = event.get("event")
            if kind == "acquire":
                resource = event.get("resource")
                if resource not in RESOURCES or resource in owner:
                    errors.append(f"{row.get('scenario')}/{row.get('policy')}: duplicate/invalid resource owner")
                else:
                    owner[resource] = name
            elif kind in ("complete", "cancel", "revoke", "lease_expire", "scc_guard_rollback_replan"):
                for resource in event.get("released", []):
                    if owner.get(resource) != name:
                        errors.append(f"{row.get('scenario')}/{row.get('policy')}: release without matching owner")
                    owner.pop(resource, None)
                if kind == "complete":
                    completed.add(name)
                if kind in ("cancel", "revoke"):
                    released.add(name)
            elif kind == "wait":
                if owner.get(event.get("resource")) != event.get("holder"):
                    errors.append(f"{row.get('scenario')}/{row.get('policy')}: wait holder mismatch")
        statuses = row.get("terminal_statuses", {})
        if row.get("completed_workflows") != sum(status == "done" for status in statuses.values()):
            errors.append(f"{row.get('scenario')}/{row.get('policy')}: completion metric mismatch")
        if completed != {name for name, status in statuses.items() if status == "done"}:
            errors.append(f"{row.get('scenario')}/{row.get('policy')}: completion trace mismatch")
        if row.get("unrecovered_deadlock") != any(status == "deadlocked" for status in statuses.values()):
            errors.append(f"{row.get('scenario')}/{row.get('policy')}: deadlock classification mismatch")
        if row.get("unrecovered_deadlock") and row.get("policy") in ("SCC_GUARD", "SAFE_REACHABILITY"):
            errors.append(f"{row.get('scenario')}/{row.get('policy')}: guarded policy deadlocked")

    by_key = {(row["scenario"], row["policy"]): row for row in rows}
    if rows:
        if not by_key.get(("opposed_order_deadlock", "NAIVE"), {}).get("unrecovered_deadlock"):
            errors.append("naive opposed-order control did not deadlock")
        if by_key.get(("opposed_order_deadlock", "SCC_GUARD"), {}).get("unrecovered_deadlock"):
            errors.append("SCC guard failed opposed-order cycle")
        if by_key.get(("opposed_order_deadlock", "SAFE_REACHABILITY"), {}).get("unrecovered_deadlock"):
            errors.append("reachability oracle failed opposed-order cycle")
        if by_key.get(("independent_workflows", "SCC_GUARD"), {}).get("makespan_ticks", 10**9) >= by_key.get(("independent_workflows", "GLOBAL_EXCLUSIVE"), {}).get("makespan_ticks", -1):
            errors.append("SCC guard did not beat global-exclusive makespan on independent work")
        hidden = by_key.get(("hidden_dependency", "SCC_GUARD"), {})
        if hidden.get("false_rejected_workflows") != 1 or "unknown" not in hidden.get("terminal_statuses", {}).values():
            errors.append("incomplete dependency was not explicitly downgraded to UNKNOWN")

    print(json.dumps({"audit": "PASS" if not errors else "FAIL", "errors": errors,
                      "trace_runs_audited": len(rows), "expected_runs": len(expected_pairs),
                      "resource_ownership_replay": True}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
