#!/usr/bin/env python3
"""Independent raw-only reconstruction for Issue #5370 T7; no candidate imports."""

import argparse
import hashlib
import json
from pathlib import Path


POLICIES = ("DEADLINE_ONLY", "NAIVE_UNBOUNDED_PI", "COMPOSED_BOUNDED_PI")


def _priority(name):
    return {"L": 1, "M": 2, "B": 2, "H": 3}[name]


def _expected(case, mode, tick_limit):
    remain = {key: case[field] for key, field in (("L", "holder_ticks"), ("M", "middle_ticks"),
              ("B", "background_ticks"), ("H", "verifier_ticks"))}
    r1, r2 = "L", ("M" if case["topology"] == "nested" else None)
    stopped = False
    cyclic = bool(case["attempt_cycle"] and mode == "NAIVE_UNBOUNDED_PI")
    trace = []
    spent = {"L": 0, "M": 0}
    boosted_ticks = {"L": 0, "M": 0}
    exhausted_at = None
    medium_seen_at = None
    finish = None
    verdict = "UNKNOWN_STALE"

    if case["attempt_cycle"]:
        trace.append({"tick": 0, "kind": "CYCLE_EDGE_ADMITTED" if cyclic else "CYCLE_EDGE_REFUSED",
                      "job": "L", "resource": "R2"})

    for now in range(tick_limit):
        if remain["H"] == 0 and remain["M"] == 0 and remain["B"] == 0 and (remain["L"] == 0 or stopped):
            trace.append({"tick": now, "kind": "ALL_WORK_COMPLETE"})
            break
        if case["holder_cancel_tick"] == now and not stopped and r1 == "L":
            stopped, r1 = True, None
            trace.append({"tick": now, "kind": "HOLDER_CANCEL_RELEASE", "job": "L", "resource": "R1"})
        if case["claim_expiry_tick"] == now:
            trace.append({"tick": now, "kind": "CLAIM_EXPIRED", "job": "H"})

        if cyclic:
            available = []
            can_run_h = False
        else:
            available = []
            if remain["L"] and not stopped:
                available.append("L")
            if remain["M"] and (case["topology"] == "direct" or r1 is None):
                available.append("M")
            if remain["B"]:
                available.append("B")
            can_run_h = bool(remain["H"] and ((case["topology"] == "direct" and r1 is None) or
                                               (case["topology"] == "nested" and r2 is None)))
            if can_run_h:
                available.append("H")

        if not available:
            trace.append({"tick": now, "kind": "DEADLOCK" if cyclic else "NO_RUNNABLE_JOB"})
            break

        rank = {name: _priority(name) for name in ("L", "M", "B", "H")}
        waiting = bool(remain["H"] and not can_run_h)
        valid = (case["claim_authenticated"] and case["claim_live"] and case["graph_complete"] and
                 (case["claim_expiry_tick"] is None or now < case["claim_expiry_tick"]))
        if mode == "COMPOSED_BOUNDED_PI" and waiting and valid:
            if case["topology"] == "direct" and r1 == "L" and spent["L"] < case["cap_ticks"]:
                rank["L"] = 3
            if case["topology"] == "nested" and r2 == "M":
                if r1 == "L" and spent["L"] < case["cap_ticks"]:
                    rank["L"] = 3
                if r1 is None and spent["M"] < case["cap_ticks"]:
                    rank["M"] = 3
        elif mode == "NAIVE_UNBOUNDED_PI" and waiting:
            if case["topology"] == "direct" and r1 == "L":
                rank["L"] = case["claimed_priority"]
            if case["topology"] == "nested" and r2 == "M":
                if r1 == "L":
                    rank["L"] = case["claimed_priority"]
                if r1 is None:
                    rank["M"] = case["claimed_priority"]

        tie = {"H": 4, "M": 3, "B": 2, "L": 1}
        selected = sorted(available, key=lambda name: (rank[name], tie[name]))[-1]
        boosted = rank[selected] > _priority(selected)
        trace.append({"tick": now, "kind": "RUN", "job": selected,
                      "effective_priority": rank[selected], "inherited": boosted})
        remain[selected] -= 1
        if boosted and selected in boosted_ticks:
            boosted_ticks[selected] += 1
            if mode == "COMPOSED_BOUNDED_PI":
                spent[selected] += 1
            if mode == "COMPOSED_BOUNDED_PI" and spent[selected] == case["cap_ticks"] and exhausted_at is None:
                exhausted_at = now + 1
                trace.append({"tick": exhausted_at, "kind": "INHERITANCE_CAP_EXHAUSTED", "job": selected})
        if selected in ("M", "B") and exhausted_at is not None and medium_seen_at is None:
            medium_seen_at = now
        if selected == "L" and remain["L"] == 0 and r1 == "L":
            r1 = None
            trace.append({"tick": now + 1, "kind": "RELEASE", "job": "L", "resource": "R1"})
        if selected == "M" and remain["M"] == 0 and r2 == "M":
            r2 = None
            trace.append({"tick": now + 1, "kind": "RELEASE", "job": "M", "resource": "R2"})
        if selected == "H" and remain["H"] == 0:
            finish = now + 1
            verdict = "ADMITTED_FRESH" if finish <= case["deadline"] else "UNKNOWN_STALE"
            trace.append({"tick": finish, "kind": verdict, "job": "H"})
    wait_after_cap = None if exhausted_at is None or medium_seen_at is None else medium_seen_at - exhausted_at
    return {"scenario_id": case["id"], "policy": mode, "events": trace,
            "verifier_finish_tick": finish, "verifier_status": verdict,
            "verifier_deadline_miss": finish is None or finish > case["deadline"],
            "cycle_edge_admitted": cyclic, "boost_ticks": boosted_ticks,
            "inheritance_cap_tick": exhausted_at,
            "medium_first_service_delay_after_cap": wait_after_cap,
            "medium_completed": remain["M"] == 0 and remain["B"] == 0,
            "background_completed": remain["B"] == 0,
            "holder_cancelled_and_released": stopped and r1 is None,
            "resource_r1_held_at_end": r1 is not None,
            "resource_r2_held_at_end": r2 is not None}


def audit(raw, scenarios):
    errors = []
    if raw.get("allocation_id") != scenarios["allocation_id"]:
        errors.append("allocation_id")
    expected = [_expected(c, p, scenarios["max_ticks"])
                for c in scenarios["scenarios"] for p in POLICIES]
    actual = raw.get("rows")
    if not isinstance(actual, list):
        errors.append("rows_not_list")
        actual = []
    if len(actual) != len(expected):
        errors.append(f"row_count:{len(actual)}!={len(expected)}")
    for i, (want, got) in enumerate(zip(expected, actual)):
        if got != want:
            errors.append(f"row_{i}:{want['scenario_id']}:{want['policy']}")
    keys = [(r.get("scenario_id"), r.get("policy")) for r in actual if isinstance(r, dict)]
    if len(keys) != len(set(keys)):
        errors.append("duplicate_case_policy")

    composed = {(r["scenario_id"], r["policy"]): r for r in actual if isinstance(r, dict)}
    for case in scenarios["scenarios"]:
        row = composed.get((case["id"], "COMPOSED_BOUNDED_PI"))
        if row is None:
            continue
        if row["verifier_status"] == "ADMITTED_FRESH" and row["verifier_deadline_miss"]:
            errors.append(f"stale_admission:{case['id']}")
        if case["attempt_cycle"] and row["cycle_edge_admitted"]:
            errors.append(f"cycle_admitted:{case['id']}")
        if case["id"] in ("forged_urgency", "claim_expires", "incomplete_wait_graph", "nonlive_blocker") and sum(row["boost_ticks"].values()):
            errors.append(f"untrusted_inheritance:{case['id']}")
        if case["holder_cancel_tick"] is not None and not row["holder_cancelled_and_released"]:
            errors.append(f"cancel_not_released:{case['id']}")
        if case["claim_expiry_tick"] is not None:
            after_expiry = [event for event in row["events"] if event.get("kind") == "RUN" and
                            event.get("inherited") and event["tick"] >= case["claim_expiry_tick"]]
            if after_expiry:
                errors.append(f"inheritance_after_expiry:{case['id']}")
            if row["resource_r1_held_at_end"] or row["resource_r2_held_at_end"]:
                errors.append(f"expired_case_resource_not_drained:{case['id']}")
        if row["medium_first_service_delay_after_cap"] is not None and row["medium_first_service_delay_after_cap"] > scenarios["fairness_bound_ticks"]:
            errors.append(f"fairness_bound:{case['id']}")
        if sum(row["boost_ticks"].values()) > case["cap_ticks"] * 2:
            errors.append(f"boost_cap:{case['id']}")
    inv = {p: 0 for p in POLICIES}
    for case in scenarios["scenarios"]:
        if case["expected_inversion"]:
            for policy in POLICIES:
                row = composed.get((case["id"], policy))
                if row is not None:
                    inv[policy] += int(row["verifier_deadline_miss"])
    if inv["COMPOSED_BOUNDED_PI"] >= inv["DEADLINE_ONLY"]:
        errors.append("no_deadline_miss_reduction")
    report = {"allocation_id": scenarios["allocation_id"], "rows_expected": len(expected),
              "rows_observed": len(actual), "errors": errors,
              "mutation_controls_expected": 9,
              "inversion_subset_deadline_misses": inv}
    return report


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    source_paths = {"candidate.py": args.freeze.parent / "candidate.py",
                    "auditor.py": Path(__file__), "scenarios.json": args.scenarios,
                    "test_construction.py": args.freeze.parent / "test_construction.py",
                    "PROTOCOL.md": args.freeze.parent / "PROTOCOL.md",
                    "README.md": args.freeze.parent / "README.md"}
    source_errors = [name for name, path in source_paths.items()
                     if sha256(path) != freeze["sha256"][name]]
    scenarios = json.loads(args.scenarios.read_text())
    raw = json.loads(args.raw.read_text())
    result = audit(raw, scenarios)
    result["source_hash_errors"] = source_errors
    result["result"] = "PASS_COMPOSITION_METHOD_SCOPED" if not result["errors"] and not source_errors else "FAIL_METHOD"
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    raise SystemExit(0 if result["result"] == "PASS_COMPOSITION_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
