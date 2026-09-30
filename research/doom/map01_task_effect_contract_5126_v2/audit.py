"""Raw-only v2 verifier. It does not import candidate or oracle modules."""
import hashlib
import json
import sys
from pathlib import Path


def _canonical_id(value):
    return type(value) is str and value.strip() == value and len(value) > 0


def audit(path):
    path = Path(path)
    doc = json.loads(path.read_text())
    errors, rows = [], doc.get("cases", [])
    if doc.get("schema") != "map01-task-effect-contract-result-v3": errors.append("schema")
    if doc.get("issue") != 5126 or doc.get("input_authority") is not False or doc.get("live_calls") != 0:
        errors.append("scope")
    if len(rows) != 13 or len({r.get("case_id") for r in rows}) != 13: errors.append("inventory")
    for row in rows:
        raw, c, o = row.get("raw", {}), row.get("candidate", {}), row.get("oracle", {})
        label = str(row.get("case_id"))
        if c != o: errors.append("candidate_oracle:" + label)
        if c.get("grants_input_authority") is not False or c.get("grants_task_authority") is not False:
            errors.append("authority:" + label)
        p = raw.get("physical") or {}
        d, u = p.get("down") or {}, p.get("up") or {}
        top_ids = [raw.get(k) for k in ("session_id", "plan_id", "actuation_id")] + [p.get("owner_id")]
        edge_ids = [d.get("source_event_id"), u.get("source_event_id")]
        times = [d.get("lower_ns"), d.get("upper_ns"), u.get("lower_ns"), u.get("upper_ns")]
        valid_physical = (
            all(_canonical_id(x) for x in top_ids + edge_ids)
            and len(set(edge_ids)) == 2 and raw.get("clock_axis_attested") is True
            and p.get("empty_release_verified") is True
            and all(_canonical_id(e.get(k)) for e in (d, u)
                    for k in ("session_id", "plan_id", "actuation_id", "owner_id", "key"))
            and all(e.get("session_id") == top_ids[0] and e.get("plan_id") == top_ids[1]
                    and e.get("actuation_id") == top_ids[2] and e.get("owner_id") == top_ids[3]
                    for e in (d, u))
            and d.get("key") == u.get("key") and all(type(t) is int for t in times)
            and 0 <= times[0] <= times[1] <= times[2] <= times[3]
        )
        if c.get("physical_actuation") != ("PHYSICAL_ACTUATION_SCOPED" if valid_physical else "UNRESOLVED"):
            errors.append("physical_reconstruction:" + label)
        sources, effects, valid, bad_source, bad_effect, rejected = (
            {x for x in edge_ids if _canonical_id(x)}, set(), [], False, False, False)
        for item in raw.get("task_effects", []):
            source, effect_id = item.get("source_event_id"), item.get("effect_id")
            source_duplicate = _canonical_id(source) and source in sources
            effect_duplicate = _canonical_id(effect_id) and effect_id in effects
            bad_source = bad_source or source_duplicate
            bad_effect = bad_effect or effect_duplicate
            okay = (
                valid_physical and _canonical_id(source) and _canonical_id(effect_id)
                and not source_duplicate and not effect_duplicate
                and item.get("session_id") == top_ids[0] and item.get("plan_id") == top_ids[1]
                and item.get("actuation_id") == top_ids[2] and item.get("scored") is True
                and item.get("scorer_independent") is True and item.get("controller_visible") is False
                and item.get("scorer_source") == "independent_progress_clock_v2"
                and item.get("kind") in ("KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS")
                and item.get("polarity") in ("useful", "harmful")
                and type(item.get("observed_ns")) is int and item.get("observed_ns", -1) >= d.get("upper_ns", 0)
            )
            if okay:
                valid.append(item); sources.add(source); effects.add(effect_id)
            else:
                rejected = True
        if bad_source: expected = "UNRESOLVED_DUPLICATE_SOURCE_EVENT"
        elif bad_effect or len(valid) > 1: expected = "UNRESOLVED_DUPLICATE_EFFECT"
        elif len(valid) == 1 and not rejected: expected = "TASK_EFFECT_SCOPED"
        elif raw.get("task_effects"): expected = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"
        else: expected = "UNRESOLVED_NO_TASK_EFFECT"
        if c.get("task_effect") != expected: errors.append("raw_effect_reconstruction:" + label)
        if c.get("task_effect") != row.get("expected_task_effect"): errors.append("expected_gate:" + label)
    return {"status": "PASS_CROSS_PLANE_SOURCE_ID_GATE" if not errors else "FAIL_CROSS_PLANE_SOURCE_ID_GATE",
            "errors": errors, "cases": len(rows), "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "formal_allocations": 1, "live_allocations": 0}


if __name__ == "__main__":
    result = audit(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("result.json"))
    Path(__file__).with_name("audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"].startswith("PASS") else 1)
