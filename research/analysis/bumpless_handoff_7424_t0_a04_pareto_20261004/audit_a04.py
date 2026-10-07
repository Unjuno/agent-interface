"""Independent saved-raw recurrence, feasibility, and optimality audit."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALPHA, RATE, REF, HORIZON, FIRST_CAP = 0.25, 0.2, 1.0, 20, 0.15
EXPECTED = {
    "no-disturbance": (0.4, 0.6, 6.023787768676, 6.0238),
    "step-disturbance-at-switch": (0.5, 0.6, 5.646697966151, 5.65),
}
PREDECESSOR_RAW_BLOB = "720a314e1859ddca9580c1fc46b751cd515ec65c"


def rollout_iae(initial_y, commands):
    y = initial_y
    states = [y]
    for command in commands:
        y = y + ALPHA * (command - y)
        states.append(y)
    return sum(abs(REF - state) for state in states), states


def audit(raw):
    errors = []
    comparator = json.loads((ROOT / "A03_COLD_MATCH.json").read_text(encoding="utf-8"))
    if comparator.get("schema") != "issue7424-a04-a03-cold-comparator-v1":
        errors.append("comparator_schema")
    if comparator.get("predecessor_raw_git_blob") != PREDECESSOR_RAW_BLOB:
        errors.append("comparator_source_pin")
    comparator_rows = {row.get("name"): row for row in comparator.get("cases", [])}
    if raw.get("schema") != "issue7424-a04-pareto-bound-raw-v1":
        errors.append("schema")
    source = raw.get("source", {})
    if source.get("base_main_sha") != "bbed04b9bf5ad7d94e20fcea212b98d19dfa6395":
        errors.append("base_main_pin")
    if source.get("predecessor_head") != "2d1c10fcdd3e0263170ba98a08dc5d1c854da9a9":
        errors.append("predecessor_head_pin")
    if source.get("predecessor_raw_git_blob") != PREDECESSOR_RAW_BLOB:
        errors.append("predecessor_raw_pin")
    rows = raw.get("cases", [])
    if len(rows) != 2 or {row.get("name") for row in rows} != set(EXPECTED):
        errors.append("case_set")
    by_name = {row.get("name"): row for row in rows}
    results = {}
    for name, (initial_y, applied, pinned_cold_iae, rounded_cold_iae) in EXPECTED.items():
        row = by_name.get(name)
        if row is None:
            continue
        if not math.isclose(row.get("initial_y", math.nan), initial_y, abs_tol=1e-12):
            errors.append(name + ":initial_state")
        if not math.isclose(row.get("actually_applied_u", math.nan), applied, abs_tol=1e-12):
            errors.append(name + ":applied_input")
        cold, oracle = row.get("cold_commands", []), row.get("oracle_commands", [])
        if len(cold) != HORIZON or len(oracle) != HORIZON:
            errors.append(name + ":command_length")
            continue
        cold_iae, _ = rollout_iae(initial_y, cold)
        oracle_iae, oracle_states = rollout_iae(initial_y, oracle)
        source_row = comparator_rows.get(name, {})
        if source_row.get("commands") != cold:
            errors.append(name + ":predecessor_cold_command_match")
        if not math.isclose(source_row.get("integrated_abs_error_21_samples", math.nan),
                            pinned_cold_iae, abs_tol=1e-12):
            errors.append(name + ":predecessor_cold_iae_pin")
        if not math.isclose(cold_iae, pinned_cold_iae, abs_tol=1e-9):
            errors.append(name + ":pinned_cold_baseline")
        if not math.isclose(row.get("replayed_cold_iae", math.nan), cold_iae, abs_tol=1e-9):
            errors.append(name + ":cold_iae_recompute")
        if not math.isclose(row.get("oracle_iae", math.nan), oracle_iae, abs_tol=1e-9):
            errors.append(name + ":oracle_iae_recompute")
        if any(not (0.0 <= u <= 1.0) for u in cold + oracle):
            errors.append(name + ":output_bounds")
        if any(abs(b-a) > RATE+1e-9 for a,b in zip([applied]+oracle[:-1], oracle)):
            errors.append(name + ":slew_bound")
        if not math.isclose(oracle[0], applied+FIRST_CAP, abs_tol=1e-12):
            errors.append(name + ":first_jump_optimal_bound")
        greedy = [oracle[0]]
        for _ in range(1, HORIZON):
            greedy.append(min(1.0, greedy[-1]+RATE))
        if any(not math.isclose(a,b,abs_tol=1e-12) for a,b in zip(oracle,greedy)):
            errors.append(name + ":not_greedy_upper_envelope")
        if any(state > REF+1e-12 for state in oracle_states):
            errors.append(name + ":positive_error_region")
        jump, cold_jump = abs(oracle[0]-applied), abs(cold[0]-applied)
        reduction = 1.0-jump/cold_jump if cold_jump else 0.0
        delta = oracle_iae-pinned_cold_iae
        rounded_delta = oracle_iae-rounded_cold_iae
        for key, value in (("oracle_first_jump",jump),("continuity_reduction",reduction),
                           ("iae_delta_vs_pinned_cold",rounded_delta)):
            if not math.isclose(row.get(key,math.nan),value,abs_tol=1e-9):
                errors.append(name+":"+key+"_summary")
        results[name] = {
            "continuity_pass": jump <= 0.75*cold_jump+1e-12,
            "tracking_no_worse": oracle_iae <= pinned_cold_iae+1e-9,
            "cold_iae": pinned_cold_iae, "oracle_iae": round(oracle_iae,12),
            "iae_delta": round(delta,12), "cold_first_jump": round(cold_jump,12),
            "oracle_first_jump": round(jump,12),
        }
    feasible = len(results)==2 and all(
        v["continuity_pass"] and v["tracking_no_worse"] for v in results.values())
    infeasible = len(results)==2 and all(
        v["continuity_pass"] and not v["tracking_no_worse"] for v in results.values())
    return {
        "schema":"issue7424-a04-pareto-bound-audit-v1", "pass":not errors,
        "errors":sorted(set(errors)),
        "classification":"FEASIBILITY_COUNTEREXAMPLE_SCOPED" if feasible and not errors else (
            "INFEASIBILITY_SUPPORTED_SCOPED" if infeasible and not errors else (
                "MIXED_OR_INCONCLUSIVE" if not errors else "AUDIT_FAIL")),
        "cases":results,
        "scope":"pinned monotone scalar envelope only; not a live-controller or task-effect result",
    }


if __name__ == "__main__":
    result=audit(json.loads((ROOT/"raw.json").read_text(encoding="utf-8")))
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["pass"] else 1)
