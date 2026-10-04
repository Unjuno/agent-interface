"""Independent formula-based audit of candidate rows and decision boundary."""
import copy
import json
import sys
from fractions import Fraction
from pathlib import Path


FIELDS = ("reference_period", "observation_period", "input_hold", "release_lag",
          "deadline", "lease", "startup_delay", "horizon")


def f(value):
    return Fraction(value)


def text(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def reference(case, factor, keep_startup):
    values = {}
    for key in FIELDS:
        values[key] = f(case[key]) * (Fraction(1) if keep_startup and key == "startup_delay" else factor)
    events = sorted((f(item["at"]) * factor, item["state"]) for item in case["events"])
    trace, now, state, first = [], values["startup_delay"], "safe", None
    while now <= values["horizon"]:
        seen = [event_state for at, event_state in events if at <= now]
        if seen:
            state = seen[-1]
        trace.append({"normalized": text(now / values["reference_period"]), "state": state})
        if state != "safe" and first is None:
            first = text(now / values["reference_period"])
        now += values["observation_period"]
    return ({key: text(value) for key, value in values.items()},
            {"trace": trace, "first_unsafe_normalized": first})


def expected_row(case, factor):
    variants = {}
    for name, multiplier, keep_startup in (
        ("baseline", Fraction(1), False),
        ("homogeneous", factor, False),
        ("fixed_startup", factor, True),
    ):
        params, trace = reference(case, multiplier, keep_startup)
        variants[name] = {"parameters": params, "trace": trace}
    return {"scenario": case["id"], "variants": variants}


def integrity_errors(spec, raw):
    errors = []
    if raw.get("schema") != "logical-time-fixed-overhead-raw-v1":
        errors.append("schema")
    if raw.get("allocation") != spec.get("allocation"):
        errors.append("allocation")
    expected = [expected_row(case, f(spec["factor"])) for case in spec["scenarios"]]
    if raw.get("rows") != expected:
        errors.append("raw_rows_reconstruction")
    return errors


def scientific_checks(spec, raw):
    rows = {row["scenario"]: row for row in raw["rows"]}
    homogeneous = all(row["variants"]["baseline"]["trace"] == row["variants"]["homogeneous"]["trace"]
                      for row in raw["rows"])
    zero = rows["zero_startup_control"]["variants"]
    zero_fixed_equal = zero["baseline"]["trace"] == zero["fixed_startup"]["trace"]
    hazard = rows["nonzero_startup_reachable_hazard"]["variants"]
    homogeneous_reaction_equal = (hazard["baseline"]["trace"]["first_unsafe_normalized"] ==
                                  hazard["homogeneous"]["trace"]["first_unsafe_normalized"])
    fixed_reaction_differs = (hazard["baseline"]["trace"]["first_unsafe_normalized"] !=
                              hazard["fixed_startup"]["trace"]["first_unsafe_normalized"])
    return {"homogeneous_traces_equal": homogeneous,
            "zero_startup_fixed_control_equal": zero_fixed_equal,
            "homogeneous_hazard_reaction_equal": homogeneous_reaction_equal,
            "fixed_startup_hazard_reaction_differs": fixed_reaction_differs}


def run_audit(spec, raw):
    errors = integrity_errors(spec, raw)
    checks = scientific_checks(spec, raw) if not errors else {}
    return errors, checks


def main():
    spec_path, raw_path, result_path = map(Path, sys.argv[1:4])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors, checks = run_audit(spec, raw)
    controls = []
    for mutation in range(4):
        changed = copy.deepcopy(raw)
        if mutation == 0:
            changed["rows"].pop()
        elif mutation == 1:
            changed["rows"][1]["variants"]["fixed_startup"]["trace"][0]["normalized"] = "999"
        elif mutation == 2:
            changed["rows"][1]["variants"]["fixed_startup"]["parameters"]["startup_delay"] = "1/2"
        else:
            changed["rows"][1]["variants"]["fixed_startup"]["trace"]["first_unsafe_normalized"] = None
        controls.append(bool(integrity_errors(spec, changed)))
    if not all(controls):
        errors.append("mutation_control")
    gate = all(checks.values()) if checks else False
    result = {"schema": "logical-time-fixed-overhead-audit-v1",
              "integrity": "PASS_RAW_RECONSTRUCTION" if not errors else "STOP_AUDIT_INTEGRITY",
              "scientific_outcome": "PASS_FIXED_OVERHEAD_DISTINGUISHED" if gate and not errors else "FAIL_OR_STOP",
              "checks": checks, "errors": errors,
              "mutation_controls": len(controls), "mutation_rejections": sum(controls)}
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors and gate else 1)


if __name__ == "__main__":
    main()
