"""Fresh audit-only reconstruction of the retained T4 logical-time raw."""
import copy
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path


FIELDS = ("reference_period", "observation_period", "input_hold", "release_lag",
          "deadline", "lease", "startup_delay", "horizon")


def rational(value):
    return Fraction(value)


def canonical(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def reconstruct_case(case, factor):
    out = {}
    for mode in ("baseline", "homogeneous", "fixed_startup"):
        scale = Fraction(1) if mode == "baseline" else factor
        times = {name: rational(case[name]) * (Fraction(1) if mode == "fixed_startup" and name == "startup_delay" else scale)
                 for name in FIELDS}
        events = sorted((rational(event["at"]) * scale, event["state"]) for event in case["events"])
        observations = []
        cursor = times["startup_delay"]
        while cursor <= times["horizon"]:
            visible = "safe"
            for at, state in events:
                if at <= cursor:
                    visible = state
                else:
                    break
            observations.append({"normalized": canonical(cursor / times["reference_period"]), "state": visible})
            cursor += times["observation_period"]
        first_unsafe = next((sample["normalized"] for sample in observations if sample["state"] != "safe"), None)
        out[mode] = {"parameters": {name: canonical(value) for name, value in times.items()},
                     "trace": {"trace": observations, "first_unsafe_normalized": first_unsafe}}
    return {"scenario": case["id"], "variants": out}


def check(spec, raw):
    errors = []
    if raw.get("schema") != "logical-time-fixed-overhead-raw-v1":
        errors.append("raw_schema")
    if raw.get("allocation") != spec.get("allocation"):
        errors.append("raw_allocation")
    expected = [reconstruct_case(case, rational(spec["factor"])) for case in spec["scenarios"]]
    if raw.get("rows") != expected:
        errors.append("rows_not_reconstructed_from_frozen_spec")
    return errors, expected


def classify(spec, raw):
    rows = {row["scenario"]: row["variants"] for row in raw["rows"]}
    equal = lambda a, b: a["trace"] == b["trace"]
    hazard = rows["nonzero_startup_reachable_hazard"]
    checks = {
        "homogeneous_traces_equal": all(equal(row["variants"]["baseline"], row["variants"]["homogeneous"])
                                         for row in raw["rows"]),
        "zero_startup_fixed_control_equal": equal(rows["zero_startup_control"]["baseline"],
                                                   rows["zero_startup_control"]["fixed_startup"]),
        "homogeneous_hazard_reaction_equal": hazard["baseline"]["trace"]["first_unsafe_normalized"] ==
                                             hazard["homogeneous"]["trace"]["first_unsafe_normalized"],
        "fixed_startup_hazard_reaction_differs": hazard["baseline"]["trace"]["first_unsafe_normalized"] !=
                                                  hazard["fixed_startup"]["trace"]["first_unsafe_normalized"],
    }
    return checks


def mutation_rejections(spec, raw):
    mutated = []
    missing = copy.deepcopy(raw)
    missing["rows"].pop()
    mutated.append(missing)
    time = copy.deepcopy(raw)
    time["rows"][1]["variants"]["fixed_startup"]["trace"]["trace"][0]["normalized"] = "999"
    mutated.append(time)
    startup = copy.deepcopy(raw)
    startup["rows"][1]["variants"]["fixed_startup"]["parameters"]["startup_delay"] = "1/2"
    mutated.append(startup)
    reaction = copy.deepcopy(raw)
    reaction["rows"][1]["variants"]["fixed_startup"]["trace"]["first_unsafe_normalized"] = None
    mutated.append(reaction)
    return [bool(check(spec, item)[0]) for item in mutated]


def run(audit_input, spec, raw):
    errors, expected = check(spec, raw)
    checks = classify(spec, raw) if not errors else {}
    controls = mutation_rejections(spec, raw) if not errors else []
    if len(controls) != 4 or not all(controls):
        errors.append("mutation_controls")
    passed = not errors and all(checks.values())
    return {"schema": "logical-time-fixed-overhead-t5-audit-v1",
            "allocation": audit_input["allocation"],
            "predecessor_allocation": audit_input["predecessor_allocation"],
            "integrity": "PASS_RAW_RECONSTRUCTION" if not errors else "STOP_AUDIT_INTEGRITY",
            "scientific_outcome": "PASS_FIXED_OVERHEAD_DISTINGUISHED" if passed else "FAIL_OR_STOP",
            "checks": checks, "integrity_errors": errors,
            "reconstructed_rows": len(expected),
            "mutation_controls": len(controls), "mutation_rejections": sum(controls)}


def main():
    root = Path(__file__).resolve().parents[3]
    input_doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    spec_path, raw_path = root / input_doc["spec_path"], root / input_doc["raw_path"]
    spec_bytes, raw_bytes = spec_path.read_bytes(), raw_path.read_bytes()
    if hashlib.sha256(spec_bytes).hexdigest() != input_doc["spec_sha256"]:
        raise SystemExit("STOP: predecessor spec hash mismatch")
    if hashlib.sha256(raw_bytes).hexdigest() != input_doc["raw_sha256"]:
        raise SystemExit("STOP: predecessor raw hash mismatch")
    spec, raw = json.loads(spec_bytes), json.loads(raw_bytes)
    result = run(input_doc, spec, raw)
    out = Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["integrity"] == "PASS_RAW_RECONSTRUCTION" and
                     result["scientific_outcome"] == "PASS_FIXED_OVERHEAD_DISTINGUISHED" else 1)


if __name__ == "__main__":
    main()
