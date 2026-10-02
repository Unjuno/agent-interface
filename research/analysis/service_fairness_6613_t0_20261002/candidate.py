"""One-shot finite queue candidate; imports no private effect oracle."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ALLOCATION = "LONG-HORIZON-SERVICE-DEBT-6613-T0-HOSTCPU-20261002-01"
MAIN_SHA = "8dc482223d2d1f6d4a54008b15070ed85f59447f"


def _revoked(req: dict, case: dict, now: int) -> bool:
    if req.get("revoked_at") is not None and req["revoked_at"] <= now:
        return True
    return any(x["principal"] == req["principal"] and x["at"] <= now
               for x in case["revocations"])


def _denial(req: dict, case: dict, now: int) -> str | None:
    if _revoked(req, case, now):
        return "REVOKED"
    if req["authority"] is not True:
        return "NO_AUTHORITY"
    if req["joint_grant"] is not True:
        return "MISSING_JOINT_GRANT"
    if req["conflict_free"] is not True:
        return "CONFLICT"
    return None


def _choose(ready: list[dict], policy: str, bypass: dict[str, int]) -> dict:
    if policy in ("fifo", "batch2"):
        return min(ready, key=lambda x: (x["arrival"], x["id"]))
    if policy == "fastest":
        return min(ready, key=lambda x: (x["service"], x["arrival"], x["id"]))
    if policy == "service_debt":
        return min(ready, key=lambda x: (-bypass.get(x["principal"], 0),
                                         x["arrival"], x["principal"], x["id"]))
    raise ValueError("unknown policy")


def simulate(case: dict, policy: str, batch_window: int, max_time: int) -> dict:
    requests = {x["id"]: dict(x) for x in case["requests"]}
    status = {rid: "PENDING" for rid in requests}
    events: list[dict] = []
    bypass: dict[str, int] = {}
    maximum_bypass = 0
    starvation_episodes = 0
    in_starvation: set[str] = set()
    released: set[int] = set()
    now = 0

    while now <= max_time:
        for at in sorted(case["safety_release_times"]):
            if at <= now and at not in released:
                events.append({"kind": "SAFETY_RELEASE", "time": at})
                released.add(at)

        for rid, req in requests.items():
            if status[rid] != "PENDING":
                continue
            reason = _denial(req, case, now)
            if reason:
                status[rid] = reason
                events.append({"kind": "EXCLUDE", "request": rid, "reason": reason, "time": now})
            elif req["arrival"] <= now and now + req["service"] > req["deadline"]:
                status[rid] = "DEADLINE_MISSED"
                events.append({"kind": "DEADLINE_MISS", "request": rid, "time": now})

        ready = [req for rid, req in requests.items()
                 if status[rid] == "PENDING" and req["arrival"] <= now
                 and not _denial(req, case, now)
                 and now + req["service"] <= req["deadline"]]
        if policy == "batch2" and now % batch_window:
            next_batch = now + (batch_window - now % batch_window)
            future = [req["arrival"] for rid, req in requests.items()
                      if status[rid] == "PENDING" and req["arrival"] > now]
            future.extend(at for at in case["safety_release_times"] if at > now and at not in released)
            now = min([next_batch, *future]) if future else next_batch
            continue

        if not ready:
            future = [req["arrival"] for rid, req in requests.items()
                      if status[rid] == "PENDING" and req["arrival"] > now]
            future.extend(at for at in case["safety_release_times"] if at > now and at not in released)
            if not future:
                break
            now = min(future)
            continue

        # Do not begin an operation that would overlap a mandatory release.
        selected = _choose(ready, policy, bypass)
        finish = now + selected["service"]
        interrupt = [at for at in case["safety_release_times"] if now < at < finish and at not in released]
        if interrupt:
            now = min(interrupt)
            continue

        active_principals = {x["principal"] for x in ready}
        for principal in list(bypass):
            if principal not in active_principals:
                bypass[principal] = 0
                in_starvation.discard(principal)
        for principal in active_principals:
            if principal == selected["principal"]:
                bypass[principal] = 0
                in_starvation.discard(principal)
            else:
                bypass[principal] = bypass.get(principal, 0) + 1
                maximum_bypass = max(maximum_bypass, bypass[principal])
                if bypass[principal] > 3 and principal not in in_starvation:
                    starvation_episodes += 1
                    in_starvation.add(principal)

        events.append({"kind": "DISPATCH", "request": selected["id"],
                       "principal": selected["principal"], "start": now, "finish": finish})
        status[selected["id"]] = "ATTEMPTED"
        now = finish

    for rid, req in requests.items():
        if status[rid] == "PENDING":
            reason = _denial(req, case, max_time)
            if reason:
                status[rid] = reason
                events.append({"kind": "EXCLUDE", "request": rid, "reason": reason, "time": max_time})
            else:
                status[rid] = "NOT_SERVED_BY_HORIZON"

    return {
        "case_id": case["id"], "policy": policy, "events": events,
        "statuses": status, "max_consecutive_bypasses": maximum_bypass,
        "starvation_episodes": starvation_episodes,
        "attempted": sum(x == "ATTEMPTED" for x in status.values()),
        "model_calls": 0,
    }


def run(fixture: dict) -> dict:
    rows = [simulate(case, policy, fixture["batch_window"], fixture["max_time"])
            for case in fixture["cases"] for policy in fixture["policies"]]
    return {"schema": "service-fairness-candidate-raw-v1", "allocation": ALLOCATION,
            "main_sha": MAIN_SHA, "policies": fixture["policies"], "rows": rows}


def main() -> None:
    out = Path(__import__("sys").argv[1]).resolve()
    if out.exists():
        raise SystemExit("STOP_OUTPUT_COLLISION")
    fixture = json.loads((ROOT / "fixture_public.json").read_text(encoding="utf-8"))
    if fixture.get("allocation") != ALLOCATION:
        raise SystemExit("STOP_ALLOCATION_MISMATCH")
    raw = run(fixture)
    out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": ALLOCATION, "rows": len(raw["rows"]), "output": str(out)}))


if __name__ == "__main__":
    main()
