"""Independent raw-only reconstruction for Issue #6655; no candidate imports."""

import json
import random
import sys
from pathlib import Path

import fixture


def _state(base, delta):
    result = dict(base)
    for key, value in delta.items():
        result[key] = value
    return result


def _expected(case_id, state):
    if case_id == "helpful_incidental_view":
        n = 1 if state.get("view") == "target_focused" else 3
        return {"correct": True, "observations": n, "recovery_cost": 0}
    if case_id == "harmful_stale_filter":
        bad = state.get("filter") == "stale_hides_required_cue"
        return {"correct": not bad, "observations": 1 if bad else 3, "recovery_cost": 2 if bad else 0}
    if case_id == "irrelevant_theme":
        return {"correct": True, "observations": 2, "recovery_cost": 0}
    if case_id == "required_saved_effect":
        return {"correct": state.get("saved_record") is True, "observations": 2, "recovery_cost": 0}
    return None


def audit(raw):
    errors = []
    if raw.get("schema") != "issue6655-incidental-state-t0-v1":
        errors.append("schema")
    if raw.get("base_main_sha") != fixture.BASE_MAIN_SHA:
        errors.append("base_main_sha")
    if raw.get("seeds") != list(fixture.SEEDS):
        errors.append("seed_set")
    by_case = {case["case_id"]: case for case in fixture.CASES}
    if raw.get("case_ids") != list(by_case):
        errors.append("case_ids")
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(by_case) * len(fixture.SEEDS):
        return {"status": "HOLD_AUDIT_INTEGRITY", "errors": errors + ["row_count"], "rows": 0}
    seen = set()
    counts = {case_id: 0 for case_id in by_case}
    effect_summaries = {case_id: {"inherit": [], "reset": []} for case_id in by_case}
    for row in rows:
        if not isinstance(row, dict):
            errors.append("row_type")
            continue
        case_id, seed = row.get("case_id"), row.get("seed")
        case = by_case.get(case_id)
        if case is None or seed not in fixture.SEEDS or (case_id, seed) in seen:
            errors.append("row_identity")
            continue
        seen.add((case_id, seed))
        counts[case_id] += 1
        index = list(by_case).index(case_id)
        expected_rng_seed = 0x6655 ^ (seed * 1009) ^ (index * 9176)
        expected_order = ["inherit", "reset"]
        random.Random(expected_rng_seed).shuffle(expected_order)
        if row.get("randomization_seed") != expected_rng_seed or row.get("assignment_order") != expected_order:
            errors.append("randomization")
        before = dict(case["baseline"])
        after = _state(before, case["delta"])
        expected_diff = [
            {"field": field, "before": before.get(field), "after": value,
             "classification": case["classification"]}
            for field, value in sorted(case["delta"].items())
        ]
        if row.get("origin_state_before") != before or row.get("origin_state_after") != after:
            errors.append("origin_state")
        if row.get("state_diff") != expected_diff:
            errors.append("state_diff")
        if row.get("task_contract") != case["task"]:
            errors.append("task_contract")
        expected_origin = {
            "completed": True,
            "required_effects": dict(case["task"].get("required_effect", {})),
        }
        if row.get("origin_task_outcome") != expected_origin:
            errors.append("origin_task_outcome")
        eligible = case["eligible"]
        if row.get("eligible") is not eligible or row.get("exclusion_reason") != case.get("exclusion_reason"):
            errors.append("eligibility")
        arms = row.get("arms")
        if not isinstance(arms, list) or len(arms) != 2 or [a.get("arm") for a in arms] != expected_order:
            errors.append("arms_or_assignment_order")
            continue
        for arm in arms:
            name = arm.get("arm")
            expected_seed = seed + (case.get("reset_seed_offset", 0) if name == "reset" else 0)
            if name not in ("inherit", "reset") or arm.get("later_task_seed") != expected_seed:
                errors.append("later_task_seed")
            if arm.get("later_task_id") != case["task"]["id"]:
                errors.append("later_task_id")
            if not eligible:
                expected_state = after
                expected_restoration = {
                    "attempted": name == "reset",
                    "complete": name != "reset" or case_id != "incomplete_restoration",
                    "cost": 0,
                }
                if arm.get("state_after_treatment") != expected_state:
                    errors.append("ineligible_state_mutated")
                if arm.get("restoration") != expected_restoration:
                    errors.append("ineligible_restore_record")
                if arm.get("outcome") is not None:
                    errors.append("ineligible_scored")
            else:
                if name == "inherit":
                    expected_state = after
                    expected_restoration = {"attempted": False, "complete": True, "cost": 0}
                elif case["classification"] == "required_effect":
                    expected_state = _state(before, case["delta"])
                    expected_restoration = {"attempted": True, "complete": True, "cost": 0}
                else:
                    expected_state = before
                    expected_restoration = {"attempted": True, "complete": True, "cost": 1}
                if arm.get("state_after_treatment") != expected_state:
                    errors.append("treatment_state")
                if arm.get("restoration") != expected_restoration:
                    errors.append("restoration_cost_or_status")
                score = _expected(case_id, expected_state)
                score["total_cost"] = score["observations"] + score["recovery_cost"] + expected_restoration["cost"]
                if arm.get("outcome") != score:
                    errors.append("outcome")
                effect_summaries[case_id][name].append(score)
        if case["classification"] == "required_effect":
            if any(a.get("state_after_treatment", {}).get("saved_record") is not True for a in arms):
                errors.append("required_effect_erased")
    if seen != {(c, s) for c in by_case for s in fixture.SEEDS}:
        errors.append("missing_rows")
    summary = {}
    for case_id, arms in effect_summaries.items():
        if arms["inherit"] and arms["reset"]:
            summary[case_id] = {
                "inherit_mean_observations": sum(x["observations"] for x in arms["inherit"]) / len(arms["inherit"]),
                "reset_mean_observations": sum(x["observations"] for x in arms["reset"]) / len(arms["reset"]),
                "inherit_correct_rate": sum(x["correct"] for x in arms["inherit"]) / len(arms["inherit"]),
                "reset_correct_rate": sum(x["correct"] for x in arms["reset"]) / len(arms["reset"]),
                "inherit_mean_total_cost": sum(x["total_cost"] for x in arms["inherit"]) / len(arms["inherit"]),
                "reset_mean_total_cost": sum(x["total_cost"] for x in arms["reset"]) / len(arms["reset"]),
            }
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "HOLD_AUDIT_INTEGRITY",
        "errors": sorted(set(errors)),
        "rows": len(rows),
        "seeds_per_case": counts,
        "eligible_cases": sum(case["eligible"] for case in fixture.CASES),
        "ineligible_cases": sum(not case["eligible"] for case in fixture.CASES),
        "descriptive_summary": summary,
        "claim_boundary": "synthetic T0 method fixture only; no real interface, human, or downstream benefit claim",
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: audit.py RAW.json OUTPUT.json", file=sys.stderr)
        return 2
    raw = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    result = audit(raw)
    out = Path(argv[1])
    try:
        with out.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, sort_keys=True, indent=2)
            stream.write("\n")
    except FileExistsError:
        print("refusing to overwrite existing output", file=sys.stderr)
        return 3
    print(f"{result['status']} errors={len(result['errors'])}")
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
