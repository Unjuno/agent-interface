#!/usr/bin/env python3
"""Independent raw-only replay audit for Issue #5424 T2."""
import json
import sys
import hashlib
from collections import defaultdict, deque
from copy import deepcopy
from pathlib import Path

POLICIES = ("NO_FREEZE", "LOCAL_CONSECUTIVE_BREAKER", "TYPED_MULTIWINDOW_BUDGET")
ROUTES = ("route-a", "route-b")
WEIGHTS = {"ok": 0, "transient": 1, "severe": 4, "catastrophic": 10}


def expected_trace(trace, policy):
    frozen_until = {}
    reason_by_route = {}
    clean_probe_run = defaultdict(int)
    recent_short = defaultdict(deque)
    recent_long = defaultdict(deque)
    parent_costs = deque()
    parent_keys = set()
    consecutive = defaultdict(int)
    expected = []
    for e in trace:
        t, route = e["t"], e["route"]
        for r in list(frozen_until):
            if policy == "TYPED_MULTIWINDOW_BUDGET":
                clean_probe_run[r] = clean_probe_run[r] + 1 if e["probes"][r] == "ok" else 0
                if t >= frozen_until[r] and clean_probe_run[r] >= 3:
                    del frozen_until[r]
                    del clean_probe_run[r]
                    reason_by_route.pop(r, None)
            elif t >= frozen_until[r]:
                del frozen_until[r]
                clean_probe_run.pop(r, None)
                reason_by_route.pop(r, None)
        held = route in frozen_until
        observed = e["primary"][route]
        recover = held or observed != "ok"
        alt = e["alternative"] if recover else None
        ok = (not held and observed == "ok") or (recover and alt == "ok")
        expected.append({"regime": e["regime"], "rep": e["rep"], "t": t,
                         "policy": policy, "route": route,
                         "decision": "FREEZE" if held else "EXECUTE",
                         "frozen_routes": sorted(frozen_until),
                         "freeze_reason": reason_by_route.get(route) if held else None,
                         "primary_observed": observed,
                         "primary_executed": None if held else observed,
                         "fallback_reason": "FROZEN" if held else ("PRIMARY_NON_OK" if recover else None),
                         "fallback_executed": alt, "completed": ok,
                         "primary_unsafe": not held and observed in ("severe", "catastrophic"),
                         "fallback_unsafe": recover and alt in ("severe", "catastrophic"),
                         "false_freeze": held and observed == "ok"})
        if held:
            continue
        if policy == "LOCAL_CONSECUTIVE_BREAKER":
            consecutive[route] = consecutive[route] + 1 if observed in ("severe", "catastrophic") else 0
            if consecutive[route] >= 2:
                consecutive[route] = 0
                frozen_until[route] = t + 12
                clean_probe_run[route] = 0
                reason_by_route[route] = "two-consecutive-severe"
        elif policy == "TYPED_MULTIWINDOW_BUDGET":
            cost = WEIGHTS[observed]
            for q, horizon in ((recent_short[route], 12), (recent_long[route], 48)):
                while q and t - q[0][0] >= horizon:
                    q.popleft()
                q.append((t, cost))
            trigger_reason = "route-short" if sum(x[1] for x in recent_short[route]) >= 8 else None
            if trigger_reason is None and sum(x[1] for x in recent_long[route]) >= 16:
                trigger_reason = "route-long"
            parent_trigger = False
            if e["incident"] and cost:
                key = (e["incident"], route)
                if key not in parent_keys:
                    parent_keys.add(key)
                    parent_costs.append((t, cost, key))
                while parent_costs and t - parent_costs[0][0] >= 48:
                    expired = parent_costs.popleft()
                    parent_keys.discard(expired[2])
                parent_trigger = sum(x[1] for x in parent_costs) >= 8
            if parent_trigger:
                for r in ROUTES:
                    if r not in frozen_until:
                        frozen_until[r] = t + 6
                        clean_probe_run[r] = 0
                        reason_by_route[r] = "common-cause-parent"
            elif trigger_reason:
                if route not in frozen_until:
                    frozen_until[route] = t + 6
                    clean_probe_run[route] = 0
                    reason_by_route[route] = trigger_reason
    return expected


def validate(inputs, outputs):
    errors = []
    indexed = defaultdict(list)
    for row in outputs:
        indexed[(row["regime"], row["rep"], row["policy"])].append(row)
    expected_keys = set()
    for regime_rep in sorted({(e["regime"], e["rep"]) for e in inputs}):
        trace = sorted((e for e in inputs if (e["regime"], e["rep"]) == regime_rep), key=lambda x: x["t"])
        for policy in POLICIES:
            key = (*regime_rep, policy)
            expected_keys.add(key)
            got = sorted(indexed.get(key, []), key=lambda x: x["t"])
            want = expected_trace(trace, policy)
            if len(got) != len(want):
                errors.append(f"row-count:{key}:{len(got)}!={len(want)}")
                continue
            for actual, calculated in zip(got, want):
                if actual != calculated:
                    fields = sorted(k for k in calculated if actual.get(k) != calculated[k])
                    errors.append(f"row-mismatch:{key}:t={calculated['t']}:fields={fields}")
                    break
    if set(indexed) != expected_keys:
        errors.append("group-key-set-mismatch")
    return errors


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def recompute_summary(outputs, inputs):
    groups = defaultdict(list)
    for row in outputs:
        groups[(row["regime"], row["policy"])].append(row)
    result = []
    repair_at = {"route_drift": (128, {"route-a"}),
                 "rare_catastrophe": (76, {"route-a"}),
                 "common_cause": (78, set(ROUTES))}
    signal_at = {"route_drift": (48, {"route-a"}),
                 "rare_catastrophe": (48, {"route-a"}),
                 "common_cause": (48, set(ROUTES))}
    inputs_by_trace = defaultdict(list)
    for event in inputs:
        inputs_by_trace[(event["regime"], event["rep"])].append(event)
    for (regime, policy), rows in sorted(groups.items()):
        reps = defaultdict(list)
        for row in rows:
            reps[row["rep"]].append(row)
        freeze_starts = max_starvation = 0
        for seq in reps.values():
            seq.sort(key=lambda x: x["t"])
            previous_frozen = False
            streak = 0
            for row in seq:
                current = row["decision"] == "FREEZE"
                freeze_starts += current and not previous_frozen
                previous_frozen = current
                streak = 0 if row["completed"] else streak + 1
                max_starvation = max(max_starvation, streak)
        repair = repair_at.get(regime)
        delays = []
        if repair:
            start, affected = repair
            for seq in reps.values():
                seq.sort(key=lambda x: x["t"])
                first = next((x["t"] for x in seq if x["t"] >= start and not affected.intersection(x["frozen_routes"])), None)
                delays.append(None if first is None else first - start)
        finite = [x for x in delays if x is not None]
        signal_start, signal_routes = signal_at.get(regime, (None, set()))
        signaled = missing_signals = post_signal = 0
        if signal_start is not None:
            for rep, seq in reps.items():
                exogenous = inputs_by_trace[(regime, rep)]
                first_signal = next((event["t"] for event in exogenous if event["t"] >= signal_start and
                                     any(event["primary"][r] in ("severe", "catastrophic") for r in signal_routes)), None)
                if first_signal is None:
                    missing_signals += 1
                else:
                    signaled += 1
                    post_signal += sum(x["primary_unsafe"] and x["route"] in signal_routes and x["t"] > first_signal for x in seq)
        result.append({"regime": regime, "policy": policy, "n": len(rows),
                       "primary_severe": sum(x["primary_unsafe"] for x in rows),
                       "fallback_severe": sum(x["fallback_unsafe"] for x in rows),
                       "completed": sum(x["completed"] for x in rows),
                       "false_freezes": sum(x["false_freeze"] for x in rows),
                       "frozen_steps": sum(x["decision"] == "FREEZE" for x in rows),
                       "freeze_starts": freeze_starts,
                       "max_starvation_steps": max_starvation,
                       "recovery_replicates": len(delays),
                       "recovered_within_12": sum(x is not None and x <= 12 for x in delays),
                       "never_recovered": sum(x is None for x in delays),
                       "max_recovery_steps": max(finite) if finite else None,
                       "signal_replicates": signaled,
                       "signal_missing_replicates": missing_signals,
                       "post_signal_primary_severe": post_signal})
    return result


def main():
    directory = Path(sys.argv[1])
    inputs = read_jsonl(directory / "inputs.jsonl")
    outputs = read_jsonl(directory / "outcomes.jsonl")
    errors = validate(inputs, outputs)
    summary = json.loads((directory / "summary.json").read_text())
    recomputed = recompute_summary(outputs, inputs)
    if summary.get("groups") != recomputed:
        errors.append("summary-does-not-match-raw-recomputation")
    if summary.get("input_rows") != len(inputs) or summary.get("outcome_rows") != len(outputs):
        errors.append("summary-row-count-mismatch")
    controls = []
    for field, value in (("decision", "FREEZE"), ("primary_unsafe", True), ("completed", True)):
        mutated = deepcopy(outputs)
        mutated[0][field] = value if mutated[0][field] != value else ("EXECUTE" if field == "decision" else not value)
        controls.append(bool(validate(inputs, mutated)))
    dropped = outputs[1:]
    controls.append(bool(validate(inputs, dropped)))
    result = {"status": "PASS_RAW_AUDIT" if not errors and all(controls) else "FAIL_RAW_AUDIT",
              "input_rows": len(inputs), "outcome_rows": len(outputs), "errors": errors[:20],
              "inputs_sha256": hashlib.sha256((directory / "inputs.jsonl").read_bytes()).hexdigest(),
              "outcomes_sha256": hashlib.sha256((directory / "outcomes.jsonl").read_bytes()).hexdigest(),
              "summary_sha256": hashlib.sha256((directory / "summary.json").read_bytes()).hexdigest(),
              "mutation_controls_rejected": sum(controls), "mutation_controls_total": len(controls)}
    (directory / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_RAW_AUDIT" else 1)


if __name__ == "__main__":
    main()
