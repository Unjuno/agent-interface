#!/usr/bin/env python3
"""Deterministic responder-capacity simulator for Issue #5435 T4."""
from fractions import Fraction
from itertools import product
import json

POLICIES = ("EMIT_ALL", "SEVERITY_ONLY", "PROBABILITY_THRESHOLD", "SIGNATURE_BATCH", "SAFE_IDENTITY_BATCH")
PATTERNS = ("burst", "paired_waves", "spaced")
CAPACITIES = (1, 2)
DEADLINES = (1, 3)
SCORE_CONDITIONS = ("calibration_like", "shifted")


def event_tape(score_condition):
    shifted_score = 0.05 if score_condition == "shifted" else 0.8
    return [
        {"alert_id": "a1-first", "entity_id": "a1", "signature": "refresh", "severity": 1,
         "actionable": True, "hard": False, "score": 0.9},
        {"alert_id": "a1-copy", "entity_id": "a1", "signature": "refresh", "severity": 1,
         "actionable": True, "hard": False, "score": 0.9},
        {"alert_id": "n1-first", "entity_id": "n1", "signature": "refresh", "severity": 1,
         "actionable": False, "hard": False, "score": 0.05},
        {"alert_id": "n1-copy", "entity_id": "n1", "signature": "refresh", "severity": 1,
         "actionable": False, "hard": False, "score": 0.05},
        {"alert_id": "a2-unknown", "entity_id": "a2", "signature": "refresh", "severity": 1,
         "actionable": True, "hard": False, "score": 0.3},
        {"alert_id": "s1-first", "entity_id": "s1", "signature": "safety", "severity": 2,
         "actionable": True, "hard": True, "score": 0.99},
        {"alert_id": "s1-copy", "entity_id": "s1", "signature": "safety", "severity": 2,
         "actionable": True, "hard": True, "score": 0.99},
        {"alert_id": "a3-shift", "entity_id": "a3", "signature": "refresh", "severity": 1,
         "actionable": True, "hard": False, "score": shifted_score},
        {"alert_id": "n2-false", "entity_id": "n2", "signature": "quota", "severity": 1,
         "actionable": False, "hard": False, "score": 0.05},
        {"alert_id": "n3-unknown", "entity_id": "n3", "signature": "quota", "severity": 1,
         "actionable": False, "hard": False, "score": None},
    ]


def arrival(index, pattern):
    if pattern == "burst":
        return 0
    if pattern == "paired_waves":
        return index // 2
    return index


def select(alerts, policy):
    published, suppressed = [], []
    seen_entities, seen_signatures = set(), set()
    for event in alerts:
        hard = event["hard"]
        score = event["score"]
        low_confidence = score is not None and score <= 0.1
        keep = True
        if policy == "SEVERITY_ONLY":
            keep = event["severity"] >= 2
        elif policy == "PROBABILITY_THRESHOLD":
            keep = hard or not (event["severity"] < 2 and low_confidence)
        elif policy == "SIGNATURE_BATCH":
            keep = hard or not (event["severity"] < 2 and low_confidence
                                and event["signature"] in seen_signatures)
        elif policy == "SAFE_IDENTITY_BATCH":
            keep = hard or not (event["severity"] < 2 and low_confidence
                                and event["entity_id"] in seen_entities)
        if keep:
            published.append(event)
            seen_entities.add(event["entity_id"])
            seen_signatures.add(event["signature"])
        else:
            suppressed.append(event)
    return published, suppressed


def run_stream(pattern, capacity, deadline, score_condition, policy):
    alerts = event_tape(score_condition)
    for i, event in enumerate(alerts):
        event["arrival"] = arrival(i, pattern)
        event["expires"] = event["arrival"] + deadline
    published, suppressed = select(alerts, policy)
    pending = list(published)
    served, expired = [], []
    response_ticks = {}
    final_tick = max(event["arrival"] for event in alerts) + deadline
    for tick in range(final_tick + 1):
        for event in list(pending):
            if event["expires"] < tick:
                expired.append(event)
                pending.remove(event)
        available = [event for event in pending if event["arrival"] <= tick]
        available.sort(key=lambda e: (not e["hard"], e["expires"], e["arrival"], e["alert_id"]))
        for event in available[:capacity]:
            served.append(event)
            pending.remove(event)
            response_ticks[event["alert_id"]] = tick
    expired.extend(pending)

    actionable_entities = {e["entity_id"] for e in alerts if e["actionable"]}
    hard_entities = {e["entity_id"] for e in alerts if e["hard"] and e["actionable"]}
    responded_entities = {e["entity_id"] for e in served if e["actionable"]}
    hard_responded = {e["entity_id"] for e in served if e["hard"] and e["actionable"]}
    first_arrival = {entity: min(e["arrival"] for e in alerts if e["entity_id"] == entity)
                     for entity in actionable_entities}
    entity_response = {}
    for entity in actionable_entities & responded_entities:
        entity_response[entity] = min(response_ticks[e["alert_id"]] - first_arrival[entity]
                                       for e in served if e["entity_id"] == entity and e["actionable"])
    latencies = list(entity_response.values())
    hard_latencies = [entity_response[e] for e in hard_entities if e in entity_response]
    return {
        "policy": policy,
        "published_ids": [e["alert_id"] for e in published],
        "suppressed_ids": [e["alert_id"] for e in suppressed],
        "served_ids": [e["alert_id"] for e in served],
        "expired_ids": [e["alert_id"] for e in expired],
        "response_tick_by_alert": response_ticks,
        "actionable_entity_count": len(actionable_entities),
        "actionable_missed_entities": sorted(actionable_entities - responded_entities),
        "hard_actionable_missed_entities": sorted(hard_entities - hard_responded),
        "low_actionable_missed_entities": sorted((actionable_entities - hard_entities) - responded_entities),
        "mean_unique_actionable_latency": (str(Fraction(sum(latencies), len(latencies))) if latencies else None),
        "max_hard_latency": max(hard_latencies) if hard_latencies else None,
        "published_nonactionable": sum(not e["actionable"] for e in published),
        "served_nonactionable": sum(not e["actionable"] for e in served),
        "suppressed_hard": sum(e["hard"] for e in suppressed),
        "preserved_unknown": sum(e["score"] is None for e in published),
    }


def make_runs():
    rows = []
    for index, (pattern, capacity, deadline, score_condition) in enumerate(
            product(PATTERNS, CAPACITIES, DEADLINES, SCORE_CONDITIONS)):
        scenario_id = f"stream-{index:02d}"
        results = [run_stream(pattern, capacity, deadline, score_condition, policy) for policy in POLICIES]
        rows.append({"scenario_id": scenario_id, "pattern": pattern, "capacity": capacity,
                     "deadline_ticks": deadline, "score_condition": score_condition,
                     "events": event_tape(score_condition), "policies": results})
    return rows


def decision(rows):
    safe = {row["scenario_id"]: next(p for p in row["policies"] if p["policy"] == "SAFE_IDENTITY_BATCH")
            for row in rows}
    all_rows = {row["scenario_id"]: next(p for p in row["policies"] if p["policy"] == "EMIT_ALL")
                for row in rows}
    miss_guard = all(len(safe[k]["actionable_missed_entities"]) <= len(all_rows[k]["actionable_missed_entities"])
                     for k in safe)
    hard_guard = all(safe[k]["max_hard_latency"] is None
                     or all_rows[k]["max_hard_latency"] is not None
                     and safe[k]["max_hard_latency"] <= all_rows[k]["max_hard_latency"] for k in safe)
    hard_suppression = sum(row["suppressed_hard"] for row in safe.values())
    safe_nonactionable = sum(row["published_nonactionable"] for row in safe.values())
    all_nonactionable = sum(row["published_nonactionable"] for row in all_rows.values())
    burden_guard = safe_nonactionable * 10 <= all_nonactionable * 9
    passed = miss_guard and hard_guard and hard_suppression == 0 and burden_guard
    return {"model_gate": "PASS" if passed else "FAIL",
            "no_more_actionable_misses_per_stream": miss_guard,
            "hard_latency_no_worse_per_stream": hard_guard,
            "hard_alerts_suppressed": hard_suppression,
            "published_nonactionable_safe_identity": safe_nonactionable,
            "published_nonactionable_emit_all": all_nonactionable,
            "at_least_10_percent_nonactionable_burden_reduction": burden_guard,
            "scope": "deterministic authored alert/responder model only; real fatigue remains untested"}


def main():
    rows = make_runs()
    print(json.dumps({"schema": "issue-5435-alert-capacity-t4-v1", "scenario_count": len(rows),
                      "policy_stream_count": sum(len(row["policies"]) for row in rows),
                      "policies": list(POLICIES), "decision": decision(rows), "streams": rows},
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
