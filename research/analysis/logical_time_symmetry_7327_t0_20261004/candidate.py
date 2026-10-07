import json
import sys
from fractions import Fraction


def q(value):
    return Fraction(value)


def s(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def transformed(case, factor, fixed=None, unit_convert=False):
    factor = q(factor)
    result = dict(case)
    for key in ("observation_period", "input_hold", "release_lag", "deadline", "lease", "startup_delay", "horizon"):
        if key != fixed:
            result[key] = s(q(case[key]) * factor)
    result["events"] = [{"at": s(q(e["at"]) * factor), "state": e["state"]} for e in case["events"]]
    if unit_convert:
        # Convert seconds -> milliseconds -> seconds using exact rational arithmetic.
        for key in ("observation_period", "input_hold", "release_lag", "deadline", "lease", "startup_delay", "horizon"):
            result[key] = s(q(result[key]) * 1000 / 1000)
        result["events"] = [{"at": s(q(e["at"]) * 1000 / 1000), "state": e["state"]} for e in result["events"]]
    return result


def run(case, ref_period, factor="1", fixed=None, unit_convert=False):
    scaled = transformed(case, factor, fixed, unit_convert)
    ref = q(ref_period) * q(factor)
    if fixed == "reference_period":
        ref = q(ref_period)
    period = q(scaled["observation_period"])
    startup = q(scaled["startup_delay"])
    horizon = q(scaled["horizon"])
    lease_at = q(scaled["lease"])
    hold_at = q(scaled["input_hold"])
    deadline_at = q(scaled["deadline"])
    release_lag = q(scaled["release_lag"])
    timeline = [(q(e["at"]), 1, "external_state", e["state"]) for e in scaled["events"]]
    t = startup
    while t <= horizon:
        timeline.append((t, 2, "observation", None))
        t += period
    timeline += [(hold_at, 3, "hold_deadline", None), (deadline_at, 4, "deadline", None), (lease_at, 0, "lease_expiry", None)]
    state = "safe"
    held = True
    release_at = None
    release_reason = None
    trace = [{"time": "0", "normalized": "0", "event": "ADMIT_AND_HOLD", "state": state, "held": held}]
    # Fixed ordering is lexicographic by rational timestamp, then frozen event priority.
    while timeline:
        timeline.sort(key=lambda row: (row[0], row[1]))
        now, _, kind, value = timeline.pop(0)
        if now > horizon:
            continue
        if kind == "lease_expiry" and held:
            held, release_at, release_reason = False, None, "LEASE_EXPIRY"
            trace.append({"time": s(now), "normalized": s(now / ref), "event": "RELEASE", "state": state, "held": False, "reason": release_reason})
        elif kind == "external_state":
            state = value
            trace.append({"time": s(now), "normalized": s(now / ref), "event": "EXTERNAL_STATE", "state": state, "held": held})
        elif kind == "observation":
            trace.append({"time": s(now), "normalized": s(now / ref), "event": "OBSERVATION", "state": state, "held": held})
            if held and state != "safe" and release_at is None:
                release_at = min(now + release_lag, lease_at)
                release_reason = "OBSERVED_NONSAFE_STATE"
                trace.append({"time": s(now), "normalized": s(now / ref), "event": "CANCEL_REQUEST", "state": state, "held": True})
                timeline.append((release_at, 5, "release", None))
        elif kind == "hold_deadline" and held and release_at is None:
            release_at = min(now + release_lag, lease_at)
            release_reason = "HOLD_DEADLINE"
            timeline.append((release_at, 5, "release", None))
        elif kind == "deadline":
            trace.append({"time": s(now), "normalized": s(now / ref), "event": "TASK_DEADLINE", "state": state, "held": held})
        elif kind == "release" and held:
            held = False
            trace.append({"time": s(now), "normalized": s(now / ref), "event": "RELEASE", "state": state, "held": False, "reason": release_reason})
    return {"scenario": case["id"], "factor": s(q(factor)), "fixed_parameter": fixed, "trace": trace, "released": not held}


def main(path):
    spec = json.load(open(path, encoding="utf-8"))
    rows = []
    for case in spec["scenarios"]:
        rows.append({"scenario": case["id"], "unit_representation": run(case, spec["reference_period"], unit_convert=True), "base": run(case, spec["reference_period"]), "homogeneous": [run(case, spec["reference_period"], k) for k in spec["transform_factors"]], "fixed_controls": {field: run(case, spec["reference_period"], "2", field) for field in spec["fixed_parameter_controls"]}})
    json.dump({"schema": "logical-time-candidate-raw-v1", "rows": rows}, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
