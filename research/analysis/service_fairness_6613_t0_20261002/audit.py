"""Independent reference replay and hidden-effect audit; imports no candidate."""
from __future__ import annotations


def _is_revoked(item, stream, tick):
    own = item.get("revoked_at")
    return (own is not None and own <= tick) or any(
        record["principal"] == item["principal"] and record["at"] <= tick
        for record in stream["revocations"])


def _valid(item, stream, tick):
    if _is_revoked(item, stream, tick):
        return False
    return (item["authority"] is True and item["joint_grant"] is True
            and item["conflict_free"] is True)


def _reference(stream, method, period, horizon):
    items = {x["id"]: dict(x) for x in stream["requests"]}
    state = {key: "PENDING" for key in items}
    ledger = []
    strikes = {}
    peak = 0
    episodes = 0
    warned = set()
    released = set()
    tick = 0

    while tick <= horizon:
        due_release = [x for x in stream["safety_release_times"] if x <= tick and x not in released]
        for moment in sorted(due_release):
            ledger.append({"kind": "SAFETY_RELEASE", "time": moment})
            released.add(moment)

        for key, item in items.items():
            if state[key] != "PENDING":
                continue
            if _is_revoked(item, stream, tick):
                state[key] = "REVOKED"
                ledger.append({"kind": "EXCLUDE", "request": key, "reason": "REVOKED", "time": tick})
            elif item["authority"] is not True:
                state[key] = "NO_AUTHORITY"
                ledger.append({"kind": "EXCLUDE", "request": key, "reason": "NO_AUTHORITY", "time": tick})
            elif item["joint_grant"] is not True:
                state[key] = "MISSING_JOINT_GRANT"
                ledger.append({"kind": "EXCLUDE", "request": key, "reason": "MISSING_JOINT_GRANT", "time": tick})
            elif item["conflict_free"] is not True:
                state[key] = "CONFLICT"
                ledger.append({"kind": "EXCLUDE", "request": key, "reason": "CONFLICT", "time": tick})
            elif item["arrival"] <= tick and tick + item["service"] > item["deadline"]:
                state[key] = "DEADLINE_MISSED"
                ledger.append({"kind": "DEADLINE_MISS", "request": key, "time": tick})

        queue = [v for key, v in items.items() if state[key] == "PENDING"
                 and v["arrival"] <= tick and _valid(v, stream, tick)
                 and tick + v["service"] <= v["deadline"]]

        if method == "batch2" and tick % period != 0:
            next_decision = tick + period - tick % period
            moments = [v["arrival"] for key, v in items.items()
                       if state[key] == "PENDING" and v["arrival"] > tick]
            moments.extend(x for x in stream["safety_release_times"] if x > tick and x not in released)
            tick = min([next_decision] + moments) if moments else next_decision
            continue

        if not queue:
            moments = [v["arrival"] for key, v in items.items()
                       if state[key] == "PENDING" and v["arrival"] > tick]
            moments.extend(x for x in stream["safety_release_times"] if x > tick and x not in released)
            if len(moments) == 0:
                break
            tick = min(moments)
            continue

        if method == "fastest":
            chosen = min(queue, key=lambda v: (v["service"], v["arrival"], v["id"]))
        elif method in ("fifo", "batch2"):
            chosen = min(queue, key=lambda v: (v["arrival"], v["id"]))
        elif method == "service_debt":
            chosen = min(queue, key=lambda v: (-strikes.get(v["principal"], 0),
                                               v["arrival"], v["principal"], v["id"]))
        else:
            raise ValueError("unknown frozen scheduler")

        end = tick + chosen["service"]
        crossing = [x for x in stream["safety_release_times"] if tick < x < end and x not in released]
        if crossing:
            tick = min(crossing)
            continue

        present = {v["principal"] for v in queue}
        for who in list(strikes):
            if who not in present:
                strikes[who] = 0
                warned.discard(who)
        for who in present:
            if who == chosen["principal"]:
                strikes[who] = 0
                warned.discard(who)
            else:
                strikes[who] = strikes.get(who, 0) + 1
                peak = max(peak, strikes[who])
                if strikes[who] > 3 and who not in warned:
                    episodes += 1
                    warned.add(who)

        ledger.append({"kind": "DISPATCH", "request": chosen["id"],
                       "principal": chosen["principal"], "start": tick, "finish": end})
        state[chosen["id"]] = "ATTEMPTED"
        tick = end

    for key, item in items.items():
        if state[key] != "PENDING":
            continue
        if _is_revoked(item, stream, horizon):
            state[key] = "REVOKED"
            ledger.append({"kind": "EXCLUDE", "request": key, "reason": "REVOKED", "time": horizon})
        elif item["authority"] is not True:
            state[key] = "NO_AUTHORITY"
            ledger.append({"kind": "EXCLUDE", "request": key, "reason": "NO_AUTHORITY", "time": horizon})
        elif item["joint_grant"] is not True:
            state[key] = "MISSING_JOINT_GRANT"
            ledger.append({"kind": "EXCLUDE", "request": key, "reason": "MISSING_JOINT_GRANT", "time": horizon})
        elif item["conflict_free"] is not True:
            state[key] = "CONFLICT"
            ledger.append({"kind": "EXCLUDE", "request": key, "reason": "CONFLICT", "time": horizon})
        else:
            state[key] = "NOT_SERVED_BY_HORIZON"

    return {"case_id": stream["id"], "policy": method, "events": ledger,
            "statuses": state, "max_consecutive_bypasses": peak,
            "starvation_episodes": episodes,
            "attempted": sum(value == "ATTEMPTED" for value in state.values()), "model_calls": 0}


def audit(public, oracle, raw):
    errors = []
    if raw.get("schema") != "service-fairness-candidate-raw-v1":
        errors.append("SCHEMA")
    if raw.get("allocation") != public.get("allocation"):
        errors.append("ALLOCATION")
    if raw.get("policies") != public.get("policies"):
        errors.append("POLICY_ORDER")
    expected_keys = [(case["id"], policy) for case in public["cases"] for policy in public["policies"]]
    indexed = {(row.get("case_id"), row.get("policy")): row
               for row in raw.get("rows", []) if isinstance(row, dict)}
    if len(indexed) != len(raw.get("rows", [])) or set(indexed) != set(expected_keys):
        errors.append("ROW_COVERAGE_OR_DUPLICATE")

    expected_success_ids = set(oracle.get("eligible_request_ids", []))
    all_ids = {item["id"] for case in public["cases"] for item in case["requests"]}
    if not expected_success_ids <= all_ids:
        errors.append("ORACLE_UNKNOWN_REQUEST")

    reconstructed = []
    for case in public["cases"]:
        for policy in public["policies"]:
            expected = _reference(case, policy, public["batch_window"], public["max_time"])
            got = indexed.get((case["id"], policy))
            if got is None:
                continue
            if got != expected:
                errors.append(f"TRACE_MISMATCH:{case['id']}:{policy}")
            if got.get("model_calls") != 0:
                errors.append(f"MODEL_CALL:{case['id']}:{policy}")
            attempt_events = [x for x in got.get("events", []) if x.get("kind") == "DISPATCH"]
            if any("verified" in x or "effect_success" in x for x in attempt_events):
                errors.append(f"ATTEMPT_AS_EFFECT:{case['id']}:{policy}")
            verified = sum(1 for event in expected["events"]
                           if event["kind"] == "DISPATCH"
                           and event["request"] in expected_success_ids
                           and oracle["exact_effect_success"].get(event["request"]) is True
                           and event["finish"] <= next(q["deadline"] for q in case["requests"]
                                                        if q["id"] == event["request"]))
            reconstructed.append({"case_id": case["id"], "policy": policy,
                                  "verified_on_time_effects": verified,
                                  "eligible_offered": sum(x["id"] in expected_success_ids for x in case["requests"]),
                                  "attempted": expected["attempted"],
                                  "max_consecutive_bypasses": expected["max_consecutive_bypasses"],
                                  "starvation_episodes": expected["starvation_episodes"]})

    asym = {row["policy"]: row for row in reconstructed
            if row["case_id"] == "asymmetric_repeated_contention"}
    baselines = ("fifo", "fastest", "batch2")
    if "service_debt" not in asym or any(name not in asym for name in baselines):
        errors.append("ASYMMETRIC_ROWS_MISSING")
    elif not all(asym["service_debt"]["max_consecutive_bypasses"] < asym[name]["max_consecutive_bypasses"]
                 for name in baselines):
        errors.append("ASYMMETRIC_BYPASS_GATE")

    for result in reconstructed:
        floor = (result["eligible_offered"] + 1) // 2
        if result["eligible_offered"] and result["verified_on_time_effects"] < floor:
            errors.append(f"ON_TIME_EFFECT_FLOOR:{result['case_id']}:{result['policy']}")

    safety_rows = [row for row in indexed.values() if row.get("case_id") == "eligibility_and_release_controls"]
    for row in safety_rows:
        releases = [i for i, event in enumerate(row["events"]) if event.get("kind") == "SAFETY_RELEASE"]
        dispatches_at_zero = [i for i, event in enumerate(row["events"])
                              if event.get("kind") == "DISPATCH" and event.get("start") == 0]
        if not releases or (dispatches_at_zero and releases[0] > min(dispatches_at_zero)):
            errors.append(f"RELEASE_ORDER:{row.get('policy')}")

    return {"status": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT",
            "rows": len(raw.get("rows", [])), "errors": errors,
            "independently_reconstructed": reconstructed,
            "mutations_rejected": {}}
