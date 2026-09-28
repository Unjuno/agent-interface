"""Independent raw-only v3 contract auditor; imports neither classifier."""
import hashlib
import json
import sys
from pathlib import Path


def _id(value):
    return type(value) is str and value != "" and value.strip() == value


def audit(path):
    path = Path(path)
    document = json.loads(path.read_text())
    rows = document.get("cases", [])
    errors = []
    if document.get("schema") != "map01-task-effect-contract-result-v4": errors.append("schema")
    if document.get("allocation") != "MAP01-TASK-EFFECT-LINEAGE-5126-20260928-03": errors.append("allocation")
    if document.get("issue") != 5126 or document.get("input_authority") is not False or document.get("live_calls") != 0:
        errors.append("scope")
    if len(rows) != 13 or len({row.get("case_id") for row in rows}) != 13: errors.append("case_inventory")
    for row in rows:
        raw, candidate, oracle = row.get("raw", {}), row.get("candidate", {}), row.get("oracle", {})
        label = str(row.get("case_id"))
        if candidate != oracle: errors.append("candidate_oracle:" + label)
        if candidate.get("grants_input_authority") is not False or candidate.get("grants_task_authority") is not False:
            errors.append("authority:" + label)
        p = raw.get("physical") or {}
        d, u = p.get("down") or {}, p.get("up") or {}
        identifiers = [raw.get(k) for k in ("session_id", "plan_id", "actuation_id")] + [p.get("owner_id")]
        physical_sources = [d.get("source_event_id"), u.get("source_event_id")]
        timestamps = [d.get("lower_ns"), d.get("upper_ns"), u.get("lower_ns"), u.get("upper_ns")]
        physical = (
            all(_id(value) for value in identifiers + physical_sources)
            and len(set(physical_sources)) == 2 and raw.get("clock_axis_attested") is True
            and p.get("empty_release_verified") is True
            and all(_id(edge.get(key)) for edge in (d, u)
                    for key in ("session_id", "plan_id", "actuation_id", "owner_id", "key"))
            and all(edge.get("session_id") == identifiers[0] and edge.get("plan_id") == identifiers[1]
                    and edge.get("actuation_id") == identifiers[2] and edge.get("owner_id") == identifiers[3]
                    for edge in (d, u))
            and d.get("key") == u.get("key") and all(type(value) is int for value in timestamps)
            and 0 <= timestamps[0] <= timestamps[1] <= timestamps[2] <= timestamps[3]
        )
        expected_physical = "PHYSICAL_ACTUATION_SCOPED" if physical else "UNRESOLVED"
        if candidate.get("physical_actuation") != expected_physical: errors.append("physical_raw:" + label)

        seen_scorer_sources, seen_effects, qualified = set(), set(), []
        cross_plane_duplicate = repeated_scorer_reference = repeated_effect_identity = False
        invalid = False
        for event in raw.get("task_effects", []):
            source_id, effect_id = event.get("source_event_id"), event.get("effect_id")
            cross_plane_duplicate |= _id(source_id) and source_id in physical_sources
            repeated_scorer_reference |= _id(source_id) and source_id in seen_scorer_sources
            repeated_effect_identity |= _id(effect_id) and effect_id in seen_effects
            valid = (
                physical and _id(source_id) and _id(effect_id)
                and source_id not in physical_sources and source_id not in seen_scorer_sources
                and effect_id not in seen_effects
                and event.get("session_id") == identifiers[0] and event.get("plan_id") == identifiers[1]
                and event.get("actuation_id") == identifiers[2] and event.get("scored") is True
                and event.get("scorer_independent") is True and event.get("controller_visible") is False
                and event.get("scorer_source") == "independent_progress_clock_v2"
                and event.get("kind") in ("KILL_COUNT_INCREASE", "DEATH_COUNT_INCREASE", "MAP_EXIT", "PROGRESS")
                and event.get("polarity") in ("useful", "harmful")
                and type(event.get("observed_ns")) is int and event.get("observed_ns", -1) >= d.get("upper_ns", 0)
            )
            if valid:
                qualified.append(event)
                seen_scorer_sources.add(source_id)
                seen_effects.add(effect_id)
            else:
                invalid = True
        if cross_plane_duplicate:
            expected_task = "UNRESOLVED_DUPLICATE_SOURCE_EVENT"
        elif repeated_scorer_reference or repeated_effect_identity or len(qualified) > 1:
            expected_task = "UNRESOLVED_DUPLICATE_EFFECT"
        elif len(qualified) == 1 and not invalid:
            expected_task = "TASK_EFFECT_SCOPED"
        elif raw.get("task_effects"):
            expected_task = "UNRESOLVED_UNBOUND_OR_INVALID_EFFECT"
        else:
            expected_task = "UNRESOLVED_NO_TASK_EFFECT"
        if candidate.get("task_effect") != expected_task: errors.append("raw_task_effect:" + label)
        if candidate.get("task_effect") != row.get("expected_task_effect"): errors.append("frozen_expectation:" + label)
    return {"status": "PASS_CROSS_PLANE_IDENTITY_CONTRACT" if not errors else "FAIL_CROSS_PLANE_IDENTITY_CONTRACT",
            "errors": errors, "cases": len(rows), "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "formal_allocations": 1, "live_allocations": 0}


if __name__ == "__main__":
    result = audit(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("result.json"))
    Path(__file__).with_name("audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"].startswith("PASS") else 1)
