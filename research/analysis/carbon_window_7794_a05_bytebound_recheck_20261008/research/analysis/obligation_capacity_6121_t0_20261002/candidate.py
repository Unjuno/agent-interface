#!/usr/bin/env python3
"""Finite synthetic cross-task obligation-capacity candidate (Issue #6121 T0)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def run_case(case: dict, fixture: dict, policy: str, fixture_hash: str) -> dict:
    obligations: dict[str, dict] = {}
    tasks: dict[str, dict] = {}
    events: list[dict] = []
    snapshots: list[dict] = []
    max_open = backlog_area = max_age = deferred_soft_total = 0
    useful_readonly = admitted_soft_total = 0

    def emit(kind: str, tick: int, **fields: object) -> None:
        events.append({"event": kind, "tick": tick, **fields})

    def create(row: dict, tick: int) -> None:
        oid = row["id"]
        if oid in obligations:
            raise ValueError(f"duplicate obligation id: {oid}")
        item = dict(row)
        item.setdefault("attempted", False)
        item["status"] = "open"
        obligations[oid] = item
        emit("create", tick, **{k: item[k] for k in ("id", "kind", "class", "resource", "owner", "generation", "created_at", "parent_id", "hard")})

    def open_items(resource: str | None = None) -> list[dict]:
        return [x for x in obligations.values() if x["status"] == "open" and (resource is None or x["resource"] == resource)]

    def new_job(tick: int, index: int) -> None:
        tid = f"{case['id']}:t{tick}:j{index}"
        tasks[tid] = {"effect": f"{tid}:effect", "release": f"{tid}:release"}
        emit("task_admitted", tick, task_id=tid)
        create({"id": f"{tid}:effect", "kind": "effect", "class": "soft", "resource": "oracle", "owner": "candidate", "generation": 0, "created_at": tick, "parent_id": tid, "hard": False}, tick)
        create({"id": f"{tid}:release", "kind": "release", "class": "soft", "resource": "owner", "owner": "candidate", "generation": 0, "created_at": tick, "parent_id": tid, "hard": False}, tick)

    for initial in case.get("initial_obligations", []):
        create(initial, initial["created_at"])

    for tick in range(fixture["horizon"]):
        for move in (x for x in case.get("transfers", []) if x["tick"] == tick):
            item = obligations[move["obligation_id"]]
            before = len(open_items())
            old_owner, old_generation = item["owner"], item["generation"]
            item["owner"] = move["new_owner"]
            item["generation"] += 1
            emit("transfer", tick, obligation_id=item["id"], old_owner=old_owner, new_owner=item["owner"], old_generation=old_generation, new_generation=item["generation"], system_open_before=before, system_open_after=len(open_items()))
        for receipt in (x for x in case.get("stale_receipts", []) if x["tick"] == tick):
            item = obligations[receipt["obligation_id"]]
            emit("stale_receipt", tick, obligation_id=item["id"], receipt_generation=receipt["receipt_generation"], current_generation=item["generation"], accepted=False)
        for timeout in (x for x in case.get("timeouts", []) if x["tick"] == tick):
            item = obligations[timeout["obligation_id"]]
            emit("timeout", tick, obligation_id=item["id"], state_before=item["status"], state_after=item["status"])

        for index in range(case["hard_releases"][tick]):
            oid = f"{case['id']}:t{tick}:hard-release:{index}"
            create({"id": oid, "kind": "release", "class": "hard", "resource": "owner", "owner": "safety-lane", "generation": 0, "created_at": tick, "parent_id": None, "hard": True}, tick)

        pre_open = len(open_items())
        pre_soft = sum(x["class"] == "soft" for x in open_items())
        offered = case["soft_arrivals"][tick]
        if policy == "LEDGER_ONLY":
            admitted = offered
        elif policy == "GLOBAL_WAIT":
            admitted = offered if pre_open == 0 else 0
        elif policy == "FIXED_CAP":
            admitted = min(offered, max(0, (fixture["fixed_cap"] - pre_open) // 2))
        else:
            admitted = min(offered, max(0, (fixture["class_cap"] - pre_soft) // 2))
        ro_offered = case["readonly_arrivals"][tick]
        ro_admitted = 0 if policy == "GLOBAL_WAIT" and pre_open > 0 else ro_offered
        emit("policy_decision", tick, policy=policy, pre_system_open=pre_open, pre_soft_open=pre_soft, offered_soft=offered, admitted_soft=admitted, deferred_soft=offered-admitted, offered_readonly=ro_offered, admitted_readonly=ro_admitted)
        deferred_soft_total += offered - admitted
        for index in range(admitted):
            new_job(tick, index)
        admitted_soft_total = sum(1 for x in events if x["event"] == "task_admitted")
        for index in range(ro_admitted):
            emit("readonly_complete", tick, readonly_id=f"{case['id']}:t{tick}:ro{index}", independently_verified=True)
            useful_readonly += 1

        # The owner resource always gives mandatory physical release priority.
        release_candidates = open_items("owner")
        if release_candidates:
            release_candidates.sort(key=lambda x: (not x["hard"], x["created_at"], x["id"]))
            item = release_candidates[0]
            item["status"] = "verified"
            emit("verify", tick, obligation_id=item["id"], resource="owner", owner=item["owner"], generation=item["generation"], terminal=True)

        oracle_candidates = [x for x in open_items("oracle") if not x["attempted"]]
        if not case["oracle_available"][tick]:
            if open_items("oracle"):
                emit("oracle_unavailable", tick, open_oracle=len(open_items("oracle")))
        elif oracle_candidates:
            oracle_candidates.sort(key=lambda x: (x["created_at"], x["id"]))
            item = oracle_candidates[0]
            result = case.get("oracle_outcomes", {}).get(item["id"], "success")
            if result == "success":
                item["status"] = "verified"
                emit("verify", tick, obligation_id=item["id"], resource="oracle", owner=item["owner"], generation=item["generation"], terminal=True)
            else:
                item["attempted"] = True
                emit("service_failed", tick, obligation_id=item["id"], resource="oracle", owner=item["owner"], generation=item["generation"], outcome=result, terminal=False)
                if item["kind"] in ("effect", "compensation"):
                    depth = item.get("depth", 0) + 1
                    child = f"{item['id']}:comp:{depth}"
                    create({"id": child, "kind": "compensation", "class": item["class"], "resource": "oracle", "owner": item["owner"], "generation": item["generation"], "created_at": tick, "parent_id": item["id"], "hard": item["hard"], "depth": depth}, tick)

        current = open_items()
        oldest = max((tick - x["created_at"] for x in current), default=0)
        snapshot = {"tick": tick, "system_open": len(current), "soft_open": sum(x["class"] == "soft" for x in current), "max_open_age": oldest}
        snapshots.append(snapshot)
        max_open = max(max_open, snapshot["system_open"])
        backlog_area += snapshot["system_open"]
        max_age = max(max_age, oldest)

    completions = 0
    for pair in tasks.values():
        if all(obligations[oid]["status"] == "verified" for oid in pair.values()):
            completions += 1
    end_open = len(open_items())
    has_oracle_gap = any(x["event"] == "oracle_unavailable" for x in events)
    if case.get("unknown_service_capacity"):
        disposition = "UNKNOWN_CAPACITY"
    elif end_open and has_oracle_gap:
        disposition = "UNRESOLVABLE_ORACLE_GAP"
    elif end_open:
        disposition = "UNKNOWN_CAPACITY"
    elif deferred_soft_total:
        disposition = "SATURATED_BUT_CONTAINED"
    else:
        disposition = "FEASIBLE_SERVICE_REGION"
    hard_delays = [next((e["tick"]-x["created_at"] for e in events if e["event"] == "verify" and e["obligation_id"] == x["id"]), None) for x in obligations.values() if x["hard"]]
    summary = {
        "max_system_open": max_open,
        "backlog_area": backlog_area,
        "max_open_age": max_age,
        "end_system_open": end_open,
        "verified_effectful_tasks": completions,
        "verified_readonly_tasks": useful_readonly,
        "useful_completions": completions + useful_readonly,
        "admitted_soft_tasks": admitted_soft_total,
        "deferred_soft_tasks": deferred_soft_total,
        "hard_release_count": sum(1 for x in obligations.values() if x["hard"]),
        "hard_release_verified": sum(1 for x in obligations.values() if x["hard"] and x["status"] == "verified"),
        "max_hard_release_delay": max((x for x in hard_delays if x is not None), default=0),
        "false_closures": 0,
        "disposition": disposition,
        "utility": completions + useful_readonly - backlog_area / 2 - max_age / 4,
    }
    return {"schema": "obligation-capacity-raw-v1", "fixture_sha256": fixture_hash, "case_id": case["id"], "policy": policy, "events": events, "snapshots": snapshots, "summary": summary}


def main(fixture_path: str, output_path: str) -> None:
    raw_fixture = Path(fixture_path).read_bytes()
    fixture = json.loads(raw_fixture)
    fixture_hash = hashlib.sha256(raw_fixture).hexdigest()
    rows = [run_case(case, fixture, policy, fixture_hash) for case in fixture["cases"] for policy in fixture["policies"]]
    Path(output_path).write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8", newline="\n")
    print(canonical({"rows": len(rows), "fixture_sha256": fixture_hash, "output_sha256": hashlib.sha256(Path(output_path).read_bytes()).hexdigest()}))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python candidate.py FIXTURE.json OUTPUT.jsonl")
    main(sys.argv[1], sys.argv[2])

