"""Independent raw-only audit; imports neither candidate nor oracle."""
import hashlib
import json
import sys
from pathlib import Path


def _canonical(value):
    return type(value) is str and len(value) > 0 and value.strip() == value


def audit(path):
    doc = json.loads(Path(path).read_text())
    rows, errors = doc.get("cases", []), []
    if doc.get("schema") != "map01-task-effect-contract-result-v2": errors.append("schema")
    if doc.get("issue") != 5126 or doc.get("input_authority") is not False or doc.get("live_calls") != 0:
        errors.append("scope")
    ids = [row.get("case_id") for row in rows]
    if len(rows) != 13 or len(set(ids)) != 13: errors.append("case_inventory")
    for row in rows:
        raw, candidate, oracle = row.get("raw", {}), row.get("candidate", {}), row.get("oracle", {})
        label = str(row.get("case_id"))
        if candidate != oracle: errors.append("candidate_oracle:" + label)
        if candidate.get("grants_input_authority") is not False or candidate.get("grants_task_authority") is not False:
            errors.append("authority:" + label)
        p = raw.get("physical") or {}
        d, u = p.get("down") or {}, p.get("up") or {}
        sid, pid, aid, owner = tuple(raw.get(k) for k in ("session_id", "plan_id", "actuation_id")) + (p.get("owner_id"),)
        edge_ids = (d.get("source_event_id"), u.get("source_event_id"))
        times = tuple(edge.get(k) for edge in (d, u) for k in ("lower_ns", "upper_ns"))
        physical_ok = (
            all(_canonical(x) for x in (sid, pid, aid, owner))
            and raw.get("clock_axis_attested") is True and p.get("empty_release_verified") is True
            and all(_canonical(edge.get(k)) for edge in (d, u)
                    for k in ("session_id", "plan_id", "actuation_id", "owner_id", "source_event_id", "key"))
            and edge_ids[0] != edge_ids[1]
            and all(edge.get("session_id") == sid and edge.get("plan_id") == pid
                    and edge.get("actuation_id") == aid and edge.get("owner_id") == owner for edge in (d, u))
            and d.get("key") == u.get("key") and all(type(t) is int for t in times)
            and 0 <= times[0] <= times[1] <= times[2] <= times[3]
        )
        if candidate.get("physical_actuation") != ("PHYSICAL_ACTUATION_SCOPED" if physical_ok else "UNRESOLVED"):
            errors.append("physical_raw_reconstruction:" + label)
        seen_effects, seen_sources, qualified, invalid, duplicate = set(), set(), [], False, False
        for event in raw.get("task_effects", []):
            eid, source = event.get("effect_id"), event.get("source_event_id")
            duplicate = duplicate or (_canonical(eid) and eid in seen_effects) or (_canonical(source) and source in seen_sources)
            ok = (physical_ok and _canonical(eid) and _canonical(source)
                  and eid not in seen_effects and source not in seen_sources
                  and event.get("session_id") == sid and event.get("plan_id") == pid
                  and event.get("actuation_id") == aid and event.get("scored") is True
                  and event.get("scorer_independent") is True and event.get("controller_visible") is False
                  and event.get("scorer_source") == "independent_progress_clock_v2"
                  and event.get("kind") in ("KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS")
                  and event.get("polarity") in ("useful", "harmful")
                  and type(event.get("observed_ns")) is int and event.get("observed_ns", -1) >= d.get("upper_ns", 0))
            if ok:
                qualified.append(event); seen_effects.add(eid); seen_sources.add(source)
            else:
                invalid = True
        if len(qualified) == 1 and not invalid: expected = "TASK_EFFECT_SCOPED"
        elif duplicate or len(qualified) > 1: expected = "UNRESOLVED_DUPLICATE_EFFECT"
        elif raw.get("task_effects"): expected = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"
        else: expected = "UNRESOLVED_NO_TASK_EFFECT"
        if candidate.get("task_effect") != expected: errors.append("effect_raw_reconstruction:" + label)
        if candidate.get("task_effect") != row.get("expected_task_effect"): errors.append("frozen_expectation:" + label)
        if candidate.get("state_feedback") and any(item.get("authority") is not False for item in candidate["state_feedback"]):
            errors.append("state_authority:" + label)
    return {"status": "PASS_STRICT_LINEAGE_FINITE_CONTRACT" if not errors else "FAIL_STRICT_LINEAGE_AUDIT",
            "errors": errors, "cases": len(rows), "result_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "formal_allocations": 1, "live_allocations": 0}


if __name__ == "__main__":
    result = audit(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("result.json"))
    Path(__file__).with_name("audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"].startswith("PASS") else 1)
