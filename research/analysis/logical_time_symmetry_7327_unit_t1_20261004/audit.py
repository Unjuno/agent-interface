"""Independent raw-only audit for explicit seconds/milliseconds invariance."""
import argparse
import copy
import json
from fractions import Fraction
from pathlib import Path


FIELDS = ("reference_period", "observation_period", "input_hold", "release_lag",
          "deadline", "lease", "startup_delay", "horizon")
SECONDS_PER_UNIT = {"s": Fraction(1), "ms": Fraction(1, 1000)}


def number(value):
    return Fraction(value)


def text(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def expected_representation(case, unit):
    seconds_per_unit = SECONDS_PER_UNIT[unit]
    times = {field:text(number(case[field]) / seconds_per_unit) for field in FIELDS}
    events = [{"at":text(number(event["at"]) / seconds_per_unit), "state":event["state"]}
              for event in case["events"]]
    return {"unit":unit, "time":times, "events":events}


def reference_trace(case):
    """Reconstruct by sampling exogenous state at each observation time."""
    period = number(case["observation_period"])
    reference = number(case["reference_period"])
    horizon = number(case["horizon"])
    lease = number(case["lease"])
    release_lag = number(case["release_lag"])
    hold_deadline = number(case["input_hold"])
    task_deadline = number(case["deadline"])
    disturbances = sorted((number(event["at"]), event["state"])
                          for event in case["events"])
    sample_times = []
    sample = number(case["startup_delay"])
    while sample <= horizon:
        sample_times.append(sample)
        sample += period

    first_unsafe_sample = None
    for sample in sample_times:
        visible = "safe"
        for when, state in disturbances:
            if when <= sample:
                visible = state
            else:
                break
        if visible != "safe":
            first_unsafe_sample = sample
            break
    if first_unsafe_sample is None:
        trigger = min(hold_deadline + release_lag, lease)
        reason = "HOLD_DEADLINE"
    else:
        trigger = min(first_unsafe_sample + release_lag, lease)
        reason = "OBSERVED_NONSAFE_STATE"
    if lease <= trigger:
        release_time, reason = lease, "LEASE_EXPIRY"
    else:
        release_time = trigger

    timeline = [(when, 1, "EXTERNAL_STATE", state) for when, state in disturbances]
    timeline.extend((when, 2, "OBSERVATION", None) for when in sample_times)
    timeline.extend([
        (hold_deadline, 3, "HOLD_DEADLINE", None),
        (task_deadline, 4, "TASK_DEADLINE", None),
        (lease, 0, "LEASE_EXPIRY", None),
        (release_time, 5, "RELEASE", reason),
    ])
    state, held = "safe", True
    trace = [{"time":"0", "normalized":"0", "event":"ADMIT_AND_HOLD",
              "state":state, "held":held}]
    for when, _, kind, value in sorted(timeline, key=lambda item:(item[0], item[1])):
        if when > horizon:
            continue
        if kind == "LEASE_EXPIRY":
            if held and when <= release_time:
                held = False
                trace.append({"time":text(when), "normalized":text(when/reference),
                              "event":"RELEASE", "state":state, "held":False,
                              "reason":"LEASE_EXPIRY"})
        elif kind == "EXTERNAL_STATE":
            state = value
            trace.append({"time":text(when), "normalized":text(when/reference),
                          "event":kind, "state":state, "held":held})
        elif kind == "OBSERVATION":
            trace.append({"time":text(when), "normalized":text(when/reference),
                          "event":kind, "state":state, "held":held})
            if held and state != "safe" and first_unsafe_sample == when:
                trace.append({"time":text(when), "normalized":text(when/reference),
                              "event":"CANCEL_REQUEST", "state":state, "held":True})
        elif kind == "TASK_DEADLINE":
            trace.append({"time":text(when), "normalized":text(when/reference),
                          "event":kind, "state":state, "held":held})
        elif kind == "RELEASE" and held and release_time != lease:
            held = False
            trace.append({"time":text(when), "normalized":text(when/reference),
                          "event":"RELEASE", "state":state, "held":False,
                          "reason":value})
    return {"trace":trace, "released":not held}


def audit(spec, raw):
    errors = []
    if tuple(spec.get("time_fields", [])) != FIELDS:
        errors.append("frozen_time_field_inventory")
    if spec.get("representations") != ["s", "ms"]:
        errors.append("frozen_unit_inventory")
    if spec.get("event_order") != ["lease_expiry", "external_state", "observation",
                                    "hold_deadline", "deadline", "release"]:
        errors.append("frozen_event_order")
    if raw.get("schema") != "logical-time-unit-candidate-raw-v1":
        return ["raw_schema"]
    rows = raw.get("rows")
    if not isinstance(rows, list) or len(rows) != len(spec["scenarios"]):
        errors.append("scenario_inventory")
    by_id = {row.get("scenario"):row for row in rows if isinstance(row, dict)}
    for case in spec["scenarios"]:
        row = by_id.get(case["id"])
        if row is None:
            errors.append("missing:" + case["id"])
            continue
        representations = row.get("representations")
        if not isinstance(representations, dict) or set(representations) != set(spec["representations"]):
            errors.append("representation_inventory:" + case["id"])
            continue
        if representations["s"].get("input") == representations["ms"].get("input"):
            errors.append("raw_inputs_not_distinct:" + case["id"])
        expected = reference_trace(case)
        for unit in spec["representations"]:
            record = representations[unit]
            if record.get("input") != expected_representation(case, unit):
                errors.append("encoded_fields:" + case["id"] + ":" + unit)
            if record.get("result") != expected:
                errors.append("trace:" + case["id"] + ":" + unit)
        if representations["s"].get("result") != representations["ms"].get("result"):
            errors.append("cross_unit_trace:" + case["id"])
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("raw", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    errors = audit(spec, raw)
    mutations = []
    controls = []
    missing = copy.deepcopy(raw)
    missing["rows"].pop()
    mutations.append(missing)
    reference = copy.deepcopy(raw)
    next(r for r in reference["rows"] if r["scenario"] == "null")["representations"]["ms"]["input"]["time"]["reference_period"] = "1001"
    mutations.append(reference)
    event = copy.deepcopy(raw)
    next(r for r in event["rows"] if r["scenario"] == "slow_drift")["representations"]["ms"]["input"]["events"][0]["at"] = "3001"
    mutations.append(event)
    label = copy.deepcopy(raw)
    next(r for r in label["rows"] if r["scenario"] == "null")["representations"]["ms"]["input"]["unit"] = "s"
    mutations.append(label)
    for mutation in mutations:
        controls.append(bool(audit(spec, mutation)))
    if not all(controls):
        errors.append("mutation_control")
    result = {
        "status":"PASS_UNIT_REPRESENTATION_SCOPED" if not errors else "FAIL_UNIT_REPRESENTATION",
        "errors":errors,
        "scenario_pairs":len(raw.get("rows", [])),
        "distinct_raw_pairs":sum(
            row.get("representations", {}).get("s", {}).get("input") !=
            row.get("representations", {}).get("ms", {}).get("input")
            for row in raw.get("rows", []) if isinstance(row, dict)),
        "mutation_controls":len(controls),
        "mutation_rejections":sum(controls),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
