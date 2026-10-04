"""Candidate transform for a finite exact-rational time-scale fixture."""
import json
import sys
from fractions import Fraction
from pathlib import Path


FIELDS = ("reference_period", "observation_period", "input_hold", "release_lag",
          "deadline", "lease", "startup_delay", "horizon")


def q(value):
    return Fraction(value)


def fmt(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def transform(case, factor, fixed_startup):
    out = {}
    for field in FIELDS:
        multiplier = Fraction(1) if fixed_startup and field == "startup_delay" else factor
        out[field] = q(case[field]) * multiplier
    out["events"] = [(q(event["at"]) * factor, event["state"]) for event in case["events"]]
    return out


def observe(case):
    events = sorted(case["events"], key=lambda event: event[0])
    samples, now = [], case["startup_delay"]
    state, first_unsafe = "safe", None
    while now <= case["horizon"]:
        for at, event_state in events:
            if at <= now:
                state = event_state
            else:
                break
        samples.append({"normalized": fmt(now / case["reference_period"]), "state": state})
        if state != "safe" and first_unsafe is None:
            first_unsafe = fmt(now / case["reference_period"])
        now += case["observation_period"]
    return {"trace": samples, "first_unsafe_normalized": first_unsafe}


def run_case(case, factor):
    variants = {
        "baseline": transform(case, Fraction(1), False),
        "homogeneous": transform(case, factor, False),
        "fixed_startup": transform(case, factor, True),
    }
    return {"scenario": case["id"], "variants": {
        name: {"parameters": {key: fmt(value) for key, value in params.items() if key != "events"},
               "trace": observe(params)} for name, params in variants.items()}}


def main():
    spec_path, output_path = map(Path, sys.argv[1:3])
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    factor = q(spec["factor"])
    raw = {"schema": "logical-time-fixed-overhead-raw-v1", "allocation": spec["allocation"],
           "rows": [run_case(case, factor) for case in spec["scenarios"]]}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"allocation": spec["allocation"], "rows": len(raw["rows"]),
                      "result": "CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
