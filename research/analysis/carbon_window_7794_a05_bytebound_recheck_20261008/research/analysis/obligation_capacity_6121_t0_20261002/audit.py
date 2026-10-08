#!/usr/bin/env python3
"""Independent raw-event auditor for Issue #6121 T0; imports no candidate code."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def inspect_row(row: dict, case: dict, fixture: dict) -> list[str]:
    errors: list[str] = []
    events = row.get("events", [])
    state: dict[str, dict] = {}
    task_ids: set[str] = set()
    readonly = 0
    service_use: dict[tuple[int, str], int] = defaultdict(int)
    decisions: dict[int, dict] = {}
    failures: list[dict] = []
    snapshots: list[dict] = []
    current_tick = -99

    def opened(resource: str | None = None) -> list[dict]:
        return [x for x in state.values() if x["status"] == "open" and (resource is None or x["resource"] == resource)]

    def finish_tick(tick: int) -> None:
        if tick < 0:
            return
        active = opened()
        snapshots.append({
            "tick": tick,
            "system_open": len(active),
            "soft_open": sum(x["class"] == "soft" for x in active),
            "max_open_age": max((tick - x["created_at"] for x in active), default=0),
        })

    for event in events:
        tick = event.get("tick")
        if not isinstance(tick, int):
            errors.append("event_without_integer_tick")
            continue
        if tick != current_tick:
            finish_tick(current_tick)
            if current_tick >= 0 and tick < current_tick:
                errors.append("event_time_reversal")
            current_tick = tick
        kind = event.get("event")
        oid = event.get("obligation_id")
        if kind == "create":
            if event.get("id") in state:
                errors.append("duplicate_obligation_id")
                continue
            item = dict(event)
            item["status"] = "open"
            item["attempted"] = False
            state[item["id"]] = item
        elif kind == "transfer":
            item = state.get(oid)
            count_before = len(opened())
            if not item or item["status"] != "open":
                errors.append("transfer_of_nonopen_obligation")
                continue
            if event.get("old_owner") != item["owner"] or event.get("old_generation") != item["generation"]:
                errors.append("transfer_source_mismatch")
            item["owner"] = event.get("new_owner")
            item["generation"] += 1
            count_after = len(opened())
            if count_before != count_after or event.get("system_open_before") != count_before or event.get("system_open_after") != count_after:
                errors.append("transfer_changed_system_outstanding")
            if event.get("new_generation") != item["generation"]:
                errors.append("transfer_generation_mismatch")
        elif kind == "stale_receipt":
            item = state.get(oid)
            if not item or item["status"] != "open":
                errors.append("stale_receipt_target_not_open")
            elif event.get("accepted") is not False or event.get("current_generation") != item["generation"] or event.get("receipt_generation", item["generation"]) >= item["generation"]:
                errors.append("stale_receipt_accepted_or_not_stale")
        elif kind == "timeout":
            item = state.get(oid)
            if not item or item["status"] != "open" or event.get("state_before") != "open" or event.get("state_after") != "open":
                errors.append("timeout_misreported_as_discharge")
        elif kind == "policy_decision":
            policy = row.get("policy")
            pre = len(opened())
            soft = sum(x["class"] == "soft" for x in opened())
            offered = case["soft_arrivals"][tick]
            if policy == "LEDGER_ONLY":
                expected = offered
            elif policy == "GLOBAL_WAIT":
                expected = offered if pre == 0 else 0
            elif policy == "FIXED_CAP":
                expected = min(offered, max(0, (fixture["fixed_cap"] - pre) // 2))
            elif policy == "CLASS_AWARE":
                expected = min(offered, max(0, (fixture["class_cap"] - soft) // 2))
            else:
                errors.append("unknown_policy")
                expected = -1
            expected_readonly = 0 if policy == "GLOBAL_WAIT" and pre > 0 else case["readonly_arrivals"][tick]
            if (event.get("pre_system_open"), event.get("pre_soft_open"), event.get("offered_soft"), event.get("admitted_soft"), event.get("deferred_soft"), event.get("offered_readonly"), event.get("admitted_readonly")) != (pre, soft, offered, expected, offered-expected, case["readonly_arrivals"][tick], expected_readonly):
                errors.append("policy_decision_replay_mismatch")
            decisions[tick] = event
        elif kind == "task_admitted":
            task_ids.add(event.get("task_id"))
        elif kind == "readonly_complete":
            if event.get("independently_verified") is not True:
                errors.append("read_only_completion_not_verified")
            readonly += 1
        elif kind in ("verify", "service_failed"):
            item = state.get(oid)
            if not item or item["status"] != "open":
                errors.append("service_of_unknown_or_closed_obligation")
                continue
            resource = event.get("resource")
            if resource != item["resource"] or event.get("generation") != item["generation"]:
                errors.append("service_identity_or_generation_mismatch")
            service_use[(tick, resource)] += 1
            if service_use[(tick, resource)] > fixture["service_capacity"].get(resource, 0):
                errors.append("service_capacity_exceeded")
            if resource == "owner":
                hard = [x for x in opened("owner") if x["hard"]]
                if hard:
                    first = min(hard, key=lambda x: (x["created_at"], x["id"]))
                    if oid != first["id"]:
                        errors.append("mandatory_release_not_prioritized")
            if kind == "verify":
                if event.get("terminal") is not True:
                    errors.append("untyped_terminal_receipt")
                item["status"] = "verified"
            else:
                if event.get("terminal") is not False or event.get("outcome") not in ("partial", "fail"):
                    errors.append("failure_laundered_as_terminal")
                item["attempted"] = True
                failures.append(event)
        elif kind == "oracle_unavailable":
            if case["oracle_available"][tick] or not opened("oracle"):
                errors.append("false_oracle_gap")
        else:
            errors.append(f"unknown_event:{kind}")

    finish_tick(current_tick)
    horizon = fixture["horizon"]
    if sorted(decisions) != list(range(horizon)):
        errors.append("missing_or_duplicate_tick_decision")
    if len(snapshots) != horizon or snapshots != row.get("snapshots"):
        errors.append("snapshot_replay_mismatch")

    created = {oid: item for oid, item in state.items()}
    for failure in failures:
        parent = created.get(failure["obligation_id"])
        children = [x for x in created.values() if x.get("parent_id") == failure["obligation_id"] and x["kind"] == "compensation" and x["created_at"] == failure["tick"]]
        if not parent or parent["status"] != "open" or len(children) != 1:
            errors.append("failed_work_dropped_or_child_missing")
    for tid in task_ids:
        pair = [x for x in created.values() if x.get("parent_id") == tid]
        if sorted(x["kind"] for x in pair) != ["effect", "release"]:
            errors.append("admitted_task_obligation_pair_mismatch")

    completed = 0
    for tid in task_ids:
        pair = {x["kind"]: x for x in created.values() if x.get("parent_id") == tid}
        if len(pair) == 2 and pair["effect"]["status"] == pair["release"]["status"] == "verified":
            completed += 1
    end_open = len(opened())
    max_open = max((x["system_open"] for x in snapshots), default=0)
    backlog_area = sum(x["system_open"] for x in snapshots)
    max_age = max((x["max_open_age"] for x in snapshots), default=0)
    deferred = sum(x.get("deferred_soft", 0) for x in decisions.values())
    # Deferred count is present on the replayed decision records, not event counters.
    deferred = sum(d.get("deferred_soft", 0) for d in decisions.values()) if decisions else 0
    # The event schema names this field deferred_soft; retain exact policy accounting.
    if any(d.get("deferred_soft") is None for d in decisions.values()):
        deferred = sum(d.get("offered_soft", 0)-d.get("admitted_soft", 0) for d in decisions.values())
    hard = [x for x in created.values() if x.get("hard")]
    delays = []
    for item in hard:
        if item["status"] == "verified":
            receipt = next(e for e in events if e.get("event") == "verify" and e.get("obligation_id") == item["id"])
            delays.append(receipt["tick"]-item["created_at"])
    gap = any(e["event"] == "oracle_unavailable" for e in events)
    if case.get("unknown_service_capacity"):
        disposition = "UNKNOWN_CAPACITY"
    elif end_open and gap:
        disposition = "UNRESOLVABLE_ORACLE_GAP"
    elif end_open:
        disposition = "UNKNOWN_CAPACITY"
    elif deferred:
        disposition = "SATURATED_BUT_CONTAINED"
    else:
        disposition = "FEASIBLE_SERVICE_REGION"
    summary = row.get("summary", {})
    expected = {
        "max_system_open": max_open,
        "backlog_area": backlog_area,
        "max_open_age": max_age,
        "end_system_open": end_open,
        "verified_effectful_tasks": completed,
        "verified_readonly_tasks": readonly,
        "useful_completions": completed+readonly,
        "admitted_soft_tasks": len(task_ids),
        "deferred_soft_tasks": deferred,
        "hard_release_count": len(hard),
        "hard_release_verified": sum(x["status"] == "verified" for x in hard),
        "max_hard_release_delay": max(delays, default=0),
        "false_closures": 0,
        "disposition": disposition,
    }
    expected["utility"] = completed + readonly - backlog_area/2 - max_age/4
    for key, value in expected.items():
        actual = summary.get(key)
        if isinstance(value, float):
            if not isinstance(actual, (float, int)) or not math.isclose(actual, value, rel_tol=0, abs_tol=1e-9):
                errors.append(f"summary_mismatch:{key}")
        elif actual != value:
            errors.append(f"summary_mismatch:{key}")
    return errors


def audit(rows: list[dict], fixture: dict) -> dict:
    errors: list[str] = []
    expected_keys = {(case["id"], policy) for case in fixture["cases"] for policy in fixture["policies"]}
    actual_keys = [(row.get("case_id"), row.get("policy")) for row in rows]
    if len(actual_keys) != len(set(actual_keys)) or set(actual_keys) != expected_keys:
        errors.append("case_policy_matrix_incomplete_or_duplicated")
    cases = {x["id"]: x for x in fixture["cases"]}
    for row in rows:
        case = cases.get(row.get("case_id"))
        if not case:
            errors.append("unknown_case")
            continue
        if row.get("schema") != "obligation-capacity-raw-v1":
            errors.append("raw_schema_mismatch")
        errors.extend(f"{row['case_id']}/{row['policy']}:{e}" for e in inspect_row(row, case, fixture))

    lookup = {(r["case_id"], r["policy"]): r["summary"] for r in rows if r.get("case_id") in cases and r.get("policy") in fixture["policies"]}
    for case_id in ("near_burst", "burst_then_drain", "heldout_alternating"):
        aware = lookup.get((case_id, "CLASS_AWARE"), {})
        ledger = lookup.get((case_id, "LEDGER_ONLY"), {})
        global_wait = lookup.get((case_id, "GLOBAL_WAIT"), {})
        if not (aware.get("max_system_open", 0) < ledger.get("max_system_open", 0) and aware.get("backlog_area", 0) < ledger.get("backlog_area", 0)):
            errors.append(f"class_gate_did_not_reduce_backlog:{case_id}")
        if not (aware.get("utility", -1e9) > ledger.get("utility", 1e9) and aware.get("utility", -1e9) > global_wait.get("utility", 1e9)):
            errors.append(f"class_gate_tradeoff_not_better:{case_id}")
    for policy in fixture["policies"]:
        if lookup.get(("below_capacity", policy), {}).get("disposition") != "FEASIBLE_SERVICE_REGION":
            errors.append(f"below_capacity_control_misclassified:{policy}")
        if lookup.get(("oracle_gap", policy), {}).get("disposition") != "UNRESOLVABLE_ORACLE_GAP":
            errors.append(f"oracle_gap_control_misclassified:{policy}")
        if lookup.get(("handoff_timeout", policy), {}).get("disposition") != "UNRESOLVABLE_ORACLE_GAP":
            errors.append(f"handoff_timeout_misclassified:{policy}")
        if lookup.get(("unknown_service_footprint", policy), {}).get("disposition") != "UNKNOWN_CAPACITY":
            errors.append(f"unknown_footprint_misclassified:{policy}")
        if lookup.get(("failed_compensation_child", policy), {}).get("disposition") != "UNKNOWN_CAPACITY":
            errors.append(f"failed_compensation_misclassified:{policy}")
        hard_summary = lookup.get(("held_release_overload", policy), {})
        if hard_summary.get("hard_release_count") != 2 or hard_summary.get("hard_release_verified") != 2 or hard_summary.get("max_hard_release_delay", 999) > 1:
            errors.append(f"mandatory_release_not_serviced:{policy}")
    return {"disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD", "errors": errors, "rows_audited": len(rows)}


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main(fixture_path: str, raw_path: str, output_path: str) -> None:
    fixture_bytes = Path(fixture_path).read_bytes()
    fixture = json.loads(fixture_bytes)
    raw_bytes = Path(raw_path).read_bytes()
    rows = load_rows(Path(raw_path))
    result = audit(rows, fixture)
    # Five in-memory corruptions are each required to be rejected by this same auditor.
    corruptions = []
    def delete_create(xs: list[dict]) -> None:
        row = next(r for r in xs if any(e["event"] == "verify" for e in r["events"]))
        oid = next(e["obligation_id"] for e in row["events"] if e["event"] == "verify")
        row["events"].remove(next(e for e in row["events"] if e["event"] == "create" and e["id"] == oid))

    def drop_hard_release(xs: list[dict]) -> None:
        row = next(r for r in xs if r["case_id"] == "held_release_overload" and r["policy"] == "CLASS_AWARE")
        row["events"].remove(next(e for e in row["events"] if e["event"] == "verify" and "hard-release" in e.get("obligation_id", "")))

    mutations = [
        ("delete_create", delete_create),
        ("transfer_as_terminal", lambda xs: next(e for r in xs if r["case_id"] == "handoff_timeout" for e in r["events"] if e["event"] == "transfer").update(event="verify")),
        ("timeout_as_terminal", lambda xs: next(e for r in xs if r["case_id"] == "handoff_timeout" for e in r["events"] if e["event"] == "timeout").update(event="verify")),
        ("drop_mandatory_release_receipt", drop_hard_release),
        ("accept_stale_receipt", lambda xs: next(e for r in xs if r["case_id"] == "handoff_timeout" for e in r["events"] if e["event"] == "stale_receipt").update(accepted=True)),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(rows)
        try:
            mutate(changed)
            rejected = bool(audit(changed, fixture)["errors"])
        except Exception:
            rejected = True
        corruptions.append({"name": name, "rejected": rejected})
    if len(corruptions) != 5 or not all(x["rejected"] for x in corruptions):
        result["errors"].append("corruption_controls_not_all_rejected")
        result["disposition"] = "FAIL_METHOD"
    result.update({
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "corruptions": corruptions,
    })
    Path(output_path).write_text(canonical(result) + "\n", encoding="utf-8", newline="\n")
    print(canonical({"disposition": result["disposition"], "rows_audited": result["rows_audited"], "error_count": len(result["errors"]), "corruption_rejections": sum(x["rejected"] for x in corruptions), "output_sha256": hashlib.sha256(Path(output_path).read_bytes()).hexdigest()}))
    if result["disposition"] != "PASS_METHOD_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: python audit.py FIXTURE.json CANDIDATE.jsonl AUDIT.json")
    main(sys.argv[1], sys.argv[2], sys.argv[3])

