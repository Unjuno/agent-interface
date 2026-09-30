#!/usr/bin/env python3
"""Frozen deterministic synthetic T2 for Issue #5424; standard library only."""
import argparse
import json
import random
from collections import defaultdict, deque
from pathlib import Path

SEED_BASE = 20260930
REPLICATES = 24
STEPS = 192
ROUTES = ("route-a", "route-b")
POLICIES = ("NO_FREEZE", "LOCAL_CONSECUTIVE_BREAKER", "TYPED_MULTIWINDOW_BUDGET")
WEIGHT = {"ok": 0, "transient": 1, "severe": 4, "catastrophic": 10}


def draw(rng, p_cat, p_severe, p_transient):
    x = rng.random()
    if x < p_cat:
        return "catastrophic"
    if x < p_cat + p_severe:
        return "severe"
    if x < p_cat + p_severe + p_transient:
        return "transient"
    return "ok"


def probs(regime, route, t, rng):
    cat, severe, transient = 0.0, 0.008, 0.07
    if regime == "route_drift" and route == "route-a" and 48 <= t < 128:
        severe = 0.30
    elif regime == "rare_catastrophe" and route == "route-a" and 49 <= t < 76:
        severe = 0.38
    elif regime == "common_cause" and 48 <= t < 78:
        severe = 0.58
    if regime == "rare_catastrophe" and route == "route-a" and t == 48:
        cat = 1.0
    return cat, severe, transient


def make_corpus():
    rows = []
    for regime in ("stationary", "route_drift", "rare_catastrophe", "common_cause"):
        for rep in range(REPLICATES):
            rng = random.Random(SEED_BASE + rep * 1009 + ("stationary", "route_drift", "rare_catastrophe", "common_cause").index(regime) * 100003)
            for t in range(STEPS):
                route = ROUTES[rng.randrange(2)]
                primary = {}
                probes = {}
                for r in ROUTES:
                    cat, severe, transient = probs(regime, r, t, rng)
                    primary[r] = draw(rng, cat, severe, transient)
                    probes[r] = draw(rng, 0.0, severe, transient)
                alt_severe = 0.20 if regime == "common_cause" and 48 <= t < 78 else 0.012
                alternative = draw(rng, 0.0, alt_severe, 0.035)
                incident = "db-outage-1" if regime == "common_cause" and 48 <= t < 78 else None
                rows.append({"regime": regime, "rep": rep, "t": t, "route": route,
                             "primary": primary, "probes": probes,
                             "alternative": alternative, "incident": incident})
    return rows


def start_freeze(state, route, t, duration, reason):
    if route not in state["until"]:
        state["until"][route] = t + duration
        state["clean"][route] = 0
        state["freeze_reason"][route] = reason
        state["freeze_starts"] += 1


def update_recovery(state, row, policy):
    for route in list(state["until"]):
        if policy == "TYPED_MULTIWINDOW_BUDGET":
            state["clean"][route] = state["clean"][route] + 1 if row["probes"][route] == "ok" else 0
            if row["t"] >= state["until"][route] and state["clean"][route] >= 3:
                del state["until"][route]
                del state["clean"][route]
                del state["freeze_reason"][route]
        elif row["t"] >= state["until"][route]:
            del state["until"][route]
            del state["clean"][route]
            del state["freeze_reason"][route]


def simulate(trace, policy):
    state = {"until": {}, "clean": {}, "freeze_reason": {}, "freeze_starts": 0,
             "consecutive": defaultdict(int), "short": defaultdict(deque),
             "long": defaultdict(deque), "parent": deque(), "parent_seen": set()}
    out = []
    for row in trace:
        update_recovery(state, row, policy)
        route = row["route"]
        frozen = route in state["until"]
        psev = row["primary"][route]
        fallback = frozen or psev != "ok"
        altsev = row["alternative"] if fallback else None
        completed = (not frozen and psev == "ok") or (fallback and altsev == "ok")
        primary_unsafe = not frozen and psev in ("severe", "catastrophic")
        alt_unsafe = fallback and altsev in ("severe", "catastrophic")
        out.append({"regime": row["regime"], "rep": row["rep"], "t": row["t"],
                    "policy": policy, "route": route, "decision": "FREEZE" if frozen else "EXECUTE",
                    "frozen_routes": sorted(state["until"]),
                    "freeze_reason": state["freeze_reason"].get(route) if frozen else None,
                    "primary_observed": psev, "primary_executed": None if frozen else psev,
                    "fallback_reason": "FROZEN" if frozen else ("PRIMARY_NON_OK" if fallback else None),
                    "fallback_executed": altsev, "completed": completed,
                    "primary_unsafe": primary_unsafe, "fallback_unsafe": alt_unsafe,
                    "false_freeze": frozen and psev == "ok"})
        if policy == "LOCAL_CONSECUTIVE_BREAKER" and not frozen:
            state["consecutive"][route] = state["consecutive"][route] + 1 if psev in ("severe", "catastrophic") else 0
            if state["consecutive"][route] >= 2:
                state["consecutive"][route] = 0
                start_freeze(state, route, row["t"], 12, "two-consecutive-severe")
        elif policy == "TYPED_MULTIWINDOW_BUDGET" and not frozen:
            cost = WEIGHT[psev]
            for window, width in (("short", 12), ("long", 48)):
                q = state[window][route]
                while q and row["t"] - q[0][0] >= width:
                    q.popleft()
                q.append((row["t"], cost))
            short_total = sum(v for _, v in state["short"][route])
            long_total = sum(v for _, v in state["long"][route])
            reason = "route-short" if short_total >= 8 else ("route-long" if long_total >= 16 else None)
            if row["incident"] and cost:
                key = (row["incident"], route)
                if key not in state["parent_seen"]:
                    state["parent_seen"].add(key)
                    state["parent"].append((row["t"], cost, key))
                while state["parent"] and row["t"] - state["parent"][0][0] >= 48:
                    old = state["parent"].popleft()
                    state["parent_seen"].discard(old[2])
                if sum(v for _, v, _ in state["parent"]) >= 8:
                    reason = "common-cause-parent"
            if reason:
                if reason == "common-cause-parent":
                    for r in ROUTES:
                        start_freeze(state, r, row["t"], 6, reason)
                else:
                    start_freeze(state, route, row["t"], 6, reason)
    return out


def summarize(rows, corpus):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["regime"], row["policy"])].append(row)
    result = []
    for (regime, policy), g in sorted(groups.items()):
        by_rep = defaultdict(list)
        for row in g:
            by_rep[row["rep"]].append(row)
        max_streak = freeze_starts = 0
        for replicate in by_rep.values():
            streak = 0
            was_frozen = False
            for row in replicate:
                streak = 0 if row["completed"] else streak + 1
                max_streak = max(max_streak, streak)
                now_frozen = row["decision"] == "FREEZE"
                freeze_starts += now_frozen and not was_frozen
                was_frozen = now_frozen
        repair = {"route_drift": (128, ("route-a",)),
                  "rare_catastrophe": (76, ("route-a",)),
                  "common_cause": (78, ROUTES)}.get(regime)
        recovery_delays = []
        if repair:
            repair_t, affected = repair
            for rep_rows in by_rep.values():
                available = next((r["t"] for r in rep_rows if r["t"] >= repair_t and
                                  not set(affected).intersection(r["frozen_routes"])), None)
                recovery_delays.append(None if available is None else available - repair_t)
        finite_delays = [x for x in recovery_delays if x is not None]
        fault_start = {"route_drift": 48, "rare_catastrophe": 48, "common_cause": 48}.get(regime)
        affected_routes = {"route_drift": {"route-a"}, "rare_catastrophe": {"route-a"},
                           "common_cause": set(ROUTES)}.get(regime, set())
        input_by_rep = defaultdict(list)
        for event in corpus:
            if event["regime"] == regime:
                input_by_rep[event["rep"]].append(event)
        after_signal = signal_reps = 0
        if fault_start is not None:
            for rep, rep_rows in by_rep.items():
                relevant = [e for e in input_by_rep[rep] if e["t"] >= fault_start]
                signal = next((e["t"] for e in relevant if any(
                    e["primary"][r] in ("severe", "catastrophic") for r in affected_routes)), None)
                if signal is not None:
                    signal_reps += 1
                    after_signal += sum(x["primary_unsafe"] and x["route"] in affected_routes and x["t"] > signal for x in rep_rows)
        result.append({"regime": regime, "policy": policy, "n": len(g),
                       "primary_severe": sum(r["primary_unsafe"] for r in g),
                       "fallback_severe": sum(r["fallback_unsafe"] for r in g),
                       "completed": sum(r["completed"] for r in g),
                       "false_freezes": sum(r["false_freeze"] for r in g),
                       "frozen_steps": sum(r["decision"] == "FREEZE" for r in g),
                       "freeze_starts": freeze_starts,
                       "max_starvation_steps": max_streak,
                       "recovery_replicates": len(recovery_delays),
                       "recovered_within_12": sum(x is not None and x <= 12 for x in recovery_delays),
                       "never_recovered": sum(x is None for x in recovery_delays),
                       "max_recovery_steps": max(finite_delays) if finite_delays else None,
                       "signal_replicates": signal_reps,
                       "signal_missing_replicates": len(by_rep) - signal_reps,
                       "post_signal_primary_severe": after_signal})
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    corpus = make_corpus()
    with (out / "inputs.jsonl").open("w") as f:
        for row in corpus:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    outcomes = []
    by_trace = defaultdict(list)
    for row in corpus:
        by_trace[(row["regime"], row["rep"])].append(row)
    for trace in by_trace.values():
        for policy in POLICIES:
            outcomes.extend(simulate(trace, policy))
    with (out / "outcomes.jsonl").open("w") as f:
        for row in outcomes:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    summary = {"seed_base": SEED_BASE, "replicates": REPLICATES, "steps": STEPS,
               "input_rows": len(corpus), "outcome_rows": len(outcomes), "groups": summarize(outcomes, corpus)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"input_rows": len(corpus), "outcome_rows": len(outcomes), "groups": summary["groups"]}, sort_keys=True))


if __name__ == "__main__":
    main()
