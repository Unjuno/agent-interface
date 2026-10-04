"""Candidate: compare exact logical traces from explicit seconds/ms inputs."""
import argparse
import json
from fractions import Fraction
from pathlib import Path


SCALE = {"s": Fraction(1), "ms": Fraction(1, 1000)}
FIELDS = ("reference_period", "observation_period", "input_hold", "release_lag",
          "deadline", "lease", "startup_delay", "horizon")


def q(value):
    return Fraction(value)


def fmt(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def encode(case, unit):
    multiplier = 1 / SCALE[unit]
    return {
        "unit": unit,
        "time": {name: fmt(q(case[name]) * multiplier) for name in FIELDS},
        "events": [{"at": fmt(q(event["at"]) * multiplier), "state": event["state"]}
                   for event in case["events"]],
    }


def canonicalize(encoded):
    if encoded.get("unit") not in SCALE:
        raise ValueError("unsupported_time_unit")
    factor = SCALE[encoded["unit"]]
    times = encoded.get("time")
    if not isinstance(times, dict) or set(times) != set(FIELDS):
        raise ValueError("time_field_inventory_mismatch")
    return {
        **{name: q(times[name]) * factor for name in FIELDS},
        "events": [(q(event["at"]) * factor, event["state"])
                   for event in encoded.get("events", [])],
    }


def simulate(case):
    p = case
    timeline = [(at, 1, "external", state) for at, state in p["events"]]
    sample = p["startup_delay"]
    while sample <= p["horizon"]:
        timeline.append((sample, 2, "observation", None))
        sample += p["observation_period"]
    timeline.extend([
        (p["input_hold"], 3, "hold_deadline", None),
        (p["deadline"], 4, "deadline", None),
        (p["lease"], 0, "lease_expiry", None),
    ])
    state, held, release_at, release_reason = "safe", True, None, None
    trace = [{"time":"0", "normalized":"0", "event":"ADMIT_AND_HOLD",
              "state":state, "held":held}]
    while timeline:
        timeline.sort(key=lambda item: (item[0], item[1]))
        now, _, kind, value = timeline.pop(0)
        if now > p["horizon"]:
            continue
        if kind == "lease_expiry" and held:
            held, release_at, release_reason = False, None, "LEASE_EXPIRY"
            trace.append({"time":fmt(now), "normalized":fmt(now / p["reference_period"]),
                          "event":"RELEASE", "state":state, "held":False,
                          "reason":release_reason})
        elif kind == "external":
            state = value
            trace.append({"time":fmt(now), "normalized":fmt(now / p["reference_period"]),
                          "event":"EXTERNAL_STATE", "state":state, "held":held})
        elif kind == "observation":
            trace.append({"time":fmt(now), "normalized":fmt(now / p["reference_period"]),
                          "event":"OBSERVATION", "state":state, "held":held})
            if held and state != "safe" and release_at is None:
                release_at = min(now + p["release_lag"], p["lease"])
                release_reason = "OBSERVED_NONSAFE_STATE"
                trace.append({"time":fmt(now), "normalized":fmt(now / p["reference_period"]),
                              "event":"CANCEL_REQUEST", "state":state, "held":True})
                timeline.append((release_at, 5, "release", None))
        elif kind == "hold_deadline" and held and release_at is None:
            release_at = min(now + p["release_lag"], p["lease"])
            release_reason = "HOLD_DEADLINE"
            timeline.append((release_at, 5, "release", None))
        elif kind == "deadline":
            trace.append({"time":fmt(now), "normalized":fmt(now / p["reference_period"]),
                          "event":"TASK_DEADLINE", "state":state, "held":held})
        elif kind == "release" and held:
            held = False
            trace.append({"time":fmt(now), "normalized":fmt(now / p["reference_period"]),
                          "event":"RELEASE", "state":state, "held":False,
                          "reason":release_reason})
    return {"trace":trace, "released":not held}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    if tuple(spec.get("time_fields", [])) != FIELDS:
        raise SystemExit("STOP: time-field inventory differs from candidate freeze")
    if spec.get("representations") != ["s", "ms"]:
        raise SystemExit("STOP: representation inventory differs from candidate freeze")
    rows = []
    for case in spec["scenarios"]:
        pair = {}
        for unit in spec["representations"]:
            encoded = encode(case, unit)
            canonical = canonicalize(encoded)
            pair[unit] = {"input":encoded, "result":simulate(canonical)}
        rows.append({"scenario":case["id"], "representations":pair})
    output = {"schema":"logical-time-unit-candidate-raw-v1", "rows":rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"rows":len(rows), "representations":spec["representations"],
                      "result":"CANDIDATE_COMPLETE"}, sort_keys=True))


if __name__ == "__main__":
    main()
