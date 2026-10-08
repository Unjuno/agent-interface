#!/usr/bin/env python3
"""Independent replay audit for the Issue #5435 T4 simulator output."""
import json
import sys
from fractions import Fraction

POLICIES = {"EMIT_ALL", "SEVERITY_ONLY", "PROBABILITY_THRESHOLD", "SIGNATURE_BATCH", "SAFE_IDENTITY_BATCH"}
PATTERNS = {"burst", "paired_waves", "spaced"}
CAPACITIES = {1, 2}
DEADLINES = {1, 3}
SCORE_CONDITIONS = {"calibration_like", "shifted"}


def expected_alerts(condition, pattern, deadline):
    score_a3 = 0.05 if condition == "shifted" else 0.8
    data = [
        ("a1-first", "a1", "refresh", 1, True, False, 0.9),
        ("a1-copy", "a1", "refresh", 1, True, False, 0.9),
        ("n1-first", "n1", "refresh", 1, False, False, 0.05),
        ("n1-copy", "n1", "refresh", 1, False, False, 0.05),
        ("a2-unknown", "a2", "refresh", 1, True, False, 0.3),
        ("s1-first", "s1", "safety", 2, True, True, 0.99),
        ("s1-copy", "s1", "safety", 2, True, True, 0.99),
        ("a3-shift", "a3", "refresh", 1, True, False, score_a3),
        ("n2-false", "n2", "quota", 1, False, False, 0.05),
        ("n3-unknown", "n3", "quota", 1, False, False, None),
    ]
    events = []
    for i, item in enumerate(data):
        if pattern == "burst":
            tick = 0
        elif pattern == "paired_waves":
            tick = i // 2
        else:
            tick = i
        aid, entity, signature, severity, actionable, hard, score = item
        events.append({"alert_id": aid, "entity_id": entity, "signature": signature,
                       "severity": severity, "actionable": actionable, "hard": hard,
                       "score": score, "arrival": tick, "expires": tick + deadline})
    return events


def independently_publish(events, policy):
    result, dropped = [], []
    prior_entities, prior_text = set(), set()
    for event in events:
        probability = event["score"]
        suppressible = event["severity"] == 1 and probability is not None and probability <= 0.1
        retain = True
        if policy == "SEVERITY_ONLY":
            retain = event["severity"] >= 2
        elif policy == "PROBABILITY_THRESHOLD":
            retain = event["hard"] or not suppressible
        elif policy == "SIGNATURE_BATCH":
            retain = event["hard"] or not (suppressible and event["signature"] in prior_text)
        elif policy == "SAFE_IDENTITY_BATCH":
            retain = event["hard"] or not (suppressible and event["entity_id"] in prior_entities)
        if retain:
            result.append(event)
            prior_entities.add(event["entity_id"])
            prior_text.add(event["signature"])
        else:
            dropped.append(event)
    return result, dropped


def replay(events, cap):
    incoming = list(events)
    processed, missed_deadline = [], []
    response_at = {}
    final_tick = max(e["arrival"] for e in events) + max(e["expires"] - e["arrival"] for e in events)
    for now in range(final_tick + 1):
        for item in incoming[:]:
            if item["expires"] < now:
                incoming.remove(item)
                missed_deadline.append(item)
        ready = [item for item in incoming if item["arrival"] <= now]
        ready.sort(key=lambda item: (item["hard"] is False, item["expires"], item["arrival"], item["alert_id"]))
        for item in ready[:cap]:
            processed.append(item)
            incoming.remove(item)
            response_at[item["alert_id"]] = now
    missed_deadline.extend(incoming)
    return processed, missed_deadline, response_at


def expected_policy(events, policy, capacity):
    retained, dropped = independently_publish(events, policy)
    served, expired, response_at = replay(retained, capacity)
    actions = {e["entity_id"] for e in events if e["actionable"]}
    hard_actions = {e["entity_id"] for e in events if e["hard"] and e["actionable"]}
    answered = {e["entity_id"] for e in served if e["actionable"]}
    hard_answered = {e["entity_id"] for e in served if e["hard"] and e["actionable"]}
    first_seen = {x: min(e["arrival"] for e in events if e["entity_id"] == x) for x in actions}
    action_lats = [min(response_at[e["alert_id"]] - first_seen[x]
                       for e in served if e["entity_id"] == x and e["actionable"])
                   for x in actions & answered]
    hard_lats = [lat for entity in hard_actions & answered
                 for lat in [min(response_at[e["alert_id"]] - first_seen[entity]
                                 for e in served if e["entity_id"] == entity and e["actionable"] and e["hard"])]
                 ]
    return {
        "policy": policy,
        "published_ids": [e["alert_id"] for e in retained],
        "suppressed_ids": [e["alert_id"] for e in dropped],
        "served_ids": [e["alert_id"] for e in served],
        "expired_ids": [e["alert_id"] for e in expired],
        "response_tick_by_alert": response_at,
        "actionable_entity_count": len(actions),
        "actionable_missed_entities": sorted(actions - answered),
        "hard_actionable_missed_entities": sorted(hard_actions - hard_answered),
        "low_actionable_missed_entities": sorted((actions - hard_actions) - answered),
        "mean_unique_actionable_latency": str(Fraction(sum(action_lats), len(action_lats))) if action_lats else None,
        "max_hard_latency": max(hard_lats) if hard_lats else None,
        "published_nonactionable": sum(not e["actionable"] for e in retained),
        "served_nonactionable": sum(not e["actionable"] for e in served),
        "suppressed_hard": sum(e["hard"] for e in dropped),
        "preserved_unknown": sum(e["score"] is None for e in retained),
    }


def check(path):
    raw = json.load(open(path, encoding="utf-8"))
    errors = []
    if raw.get("schema") != "issue-5435-alert-capacity-t4-v1":
        errors.append("schema mismatch")
    streams = raw.get("streams", [])
    expected_keys = {(p, c, d, s) for p in PATTERNS for c in CAPACITIES
                     for d in DEADLINES for s in SCORE_CONDITIONS}
    observed = set()
    for row in streams:
        try:
            key = (row["pattern"], row["capacity"], row["deadline_ticks"], row["score_condition"])
            if key in observed or key not in expected_keys:
                errors.append("duplicate or unexpected scenario key")
            observed.add(key)
            events = expected_alerts(key[3], key[0], key[2])
            if row["events"] != [{k: e[k] for k in ("alert_id", "entity_id", "signature", "severity", "actionable", "hard", "score")}
                                  for e in events]:
                errors.append(f"{row['scenario_id']}: event tape mismatch")
            policy_rows = row["policies"]
            if {p.get("policy") for p in policy_rows} != POLICIES or len(policy_rows) != len(POLICIES):
                errors.append(f"{row['scenario_id']}: policy coverage mismatch")
                continue
            for actual in policy_rows:
                expected = expected_policy(events, actual["policy"], key[1])
                if actual != expected:
                    errors.append(f"{row['scenario_id']}/{actual['policy']}: independent replay mismatch")
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append(f"malformed stream: {type(exc).__name__}: {exc}")

    if len(streams) != 24 or observed != expected_keys or raw.get("policy_stream_count") != 120:
        errors.append("factorial or policy-stream total mismatch")
    safe = {r["scenario_id"]: next(p for p in r["policies"] if p["policy"] == "SAFE_IDENTITY_BATCH")
            for r in streams}
    baseline = {r["scenario_id"]: next(p for p in r["policies"] if p["policy"] == "EMIT_ALL")
                for r in streams}
    miss_guard = all(len(safe[k]["actionable_missed_entities"]) <= len(baseline[k]["actionable_missed_entities"])
                     for k in safe)
    latency_guard = all(safe[k]["max_hard_latency"] is None
                        or baseline[k]["max_hard_latency"] is not None
                        and safe[k]["max_hard_latency"] <= baseline[k]["max_hard_latency"] for k in safe)
    hard_suppressed = sum(x["suppressed_hard"] for x in safe.values())
    safe_false = sum(x["published_nonactionable"] for x in safe.values())
    all_false = sum(x["published_nonactionable"] for x in baseline.values())
    burden_guard = safe_false * 10 <= all_false * 9
    model_pass = miss_guard and latency_guard and hard_suppressed == 0 and burden_guard
    decision = {"model_gate": "PASS" if model_pass else "FAIL",
                "no_more_actionable_misses_per_stream": miss_guard,
                "hard_latency_no_worse_per_stream": latency_guard,
                "hard_alerts_suppressed": hard_suppressed,
                "published_nonactionable_safe_identity": safe_false,
                "published_nonactionable_emit_all": all_false,
                "at_least_10_percent_nonactionable_burden_reduction": burden_guard,
                "scope": "deterministic authored alert/responder model only; real fatigue remains untested"}
    if raw.get("decision") != decision:
        errors.append("summary decision mismatch")
    return {"audit": "PASS" if not errors else "FAIL", "errors": errors,
            "scenario_count": len(streams), "policy_stream_count": sum(len(r.get("policies", [])) for r in streams),
            "decision": decision}


if __name__ == "__main__":
    print(json.dumps(check(sys.argv[1]), sort_keys=True, indent=2))
