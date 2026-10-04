import copy
import json
import sys
from fractions import Fraction


def Q(x):
    return Fraction(x)


def F(x):
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def independent_trace(case, ref, factor="1", fixed=None, unit=False):
    factor = Q(factor)
    # Reconstruct each model parameter from the frozen fixture, not candidate output.
    params = {}
    for name in ("observation_period", "input_hold", "release_lag", "deadline", "lease", "startup_delay", "horizon"):
        value = Q(case[name])
        if name != fixed:
            value *= factor
        params[name] = value
    disturbances = []
    for item in case["events"]:
        disturbances.append((Q(item["at"]) * factor, item["state"]))
    reference = Q(ref) * factor
    if unit:
        # Exact unit round-trip: the representation is multiplied and divided by 1000.
        params = {k: v * 1000 / 1000 for k, v in params.items()}
        disturbances = [(t * 1000 / 1000, state) for t, state in disturbances]
    samples = []
    sample = params["startup_delay"]
    while sample <= params["horizon"]:
        samples.append(sample)
        sample += params["observation_period"]

    # State at a sample is reconstructed by a fold over exogenous transitions.
    cancel_sample = None
    for sample in samples:
        state = "safe"
        for at, new_state in sorted(disturbances):
            if at <= sample:
                state = new_state
            else:
                break
        if state != "safe":
            cancel_sample = sample
            break

    release_candidate = None
    reason = None
    if cancel_sample is not None:
        release_candidate = min(cancel_sample + params["release_lag"], params["lease"])
        reason = "OBSERVED_NONSAFE_STATE"
    else:
        release_candidate = min(params["input_hold"] + params["release_lag"], params["lease"])
        reason = "HOLD_DEADLINE"
    if params["lease"] <= release_candidate:
        release_time, reason = params["lease"], "LEASE_EXPIRY"
    else:
        release_time = release_candidate

    def state_at(t):
        value = "safe"
        for at, new_state in sorted(disturbances):
            if at <= t:
                value = new_state
            else:
                break
        return value

    # Rebuild the visible event ledger with a separately stated precedence relation.
    items = [(t, 1, "EXTERNAL_STATE", st) for t, st in disturbances if t <= params["horizon"]]
    items += [(t, 2, "OBSERVATION", None) for t in samples]
    items += [(params["input_hold"], 3, "HOLD_DEADLINE", None),
              (params["deadline"], 4, "TASK_DEADLINE", None),
              (params["lease"], 0, "LEASE_EXPIRY", None),
              (release_time, 5, "RELEASE", reason)]
    alive = True
    trace = [{"time":"0", "normalized":"0", "event":"ADMIT_AND_HOLD", "state":"safe", "held":True}]
    for at, _, kind, value in sorted(items, key=lambda x:(x[0], x[1])):
        if at > params["horizon"]:
            continue
        current_state = state_at(at)
        if kind == "LEASE_EXPIRY":
            if alive and at <= release_time:
                alive = False
                trace.append({"time":F(at), "normalized":F(at/reference), "event":"RELEASE", "state":current_state, "held":False, "reason":"LEASE_EXPIRY"})
        elif kind == "EXTERNAL_STATE":
            trace.append({"time":F(at), "normalized":F(at/reference), "event":kind, "state":value, "held":alive})
        elif kind == "OBSERVATION":
            trace.append({"time":F(at), "normalized":F(at/reference), "event":kind, "state":current_state, "held":alive})
            if alive and current_state != "safe" and cancel_sample == at:
                trace.append({"time":F(at), "normalized":F(at/reference), "event":"CANCEL_REQUEST", "state":current_state, "held":True})
        elif kind == "HOLD_DEADLINE":
            pass
        elif kind == "TASK_DEADLINE":
            trace.append({"time":F(at), "normalized":F(at/reference), "event":kind, "state":current_state, "held":alive})
        elif kind == "RELEASE" and alive:
            if release_time == params["lease"]:
                continue  # The higher-priority lease event already emitted the release.
            alive = False
            trace.append({"time":F(at), "normalized":F(at/reference), "event":"RELEASE", "state":current_state, "held":False, "reason":value})
    return {"scenario":case["id"], "factor":F(factor), "fixed_parameter":fixed, "trace":trace, "released":not alive}


def check(spec, raw):
    errors = []
    rows = raw.get("rows")
    if raw.get("schema") != "logical-time-candidate-raw-v1" or not isinstance(rows, list):
        return ["raw_schema"]
    if len(rows) != len(spec["scenarios"]):
        errors.append("case_count")
    by_id = {r.get("scenario"): r for r in rows if isinstance(r, dict)}
    for case in spec["scenarios"]:
        row = by_id.get(case["id"])
        if row is None:
            errors.append("missing:" + case["id"])
            continue
        expected_base = independent_trace(case, spec["reference_period"])
        expected_unit = independent_trace(case, spec["reference_period"], unit=True)
        if row.get("base") != expected_base:
            errors.append("base:" + case["id"])
        if row.get("unit_representation") != expected_unit:
            errors.append("unit:" + case["id"])
        expected_hom = [independent_trace(case, spec["reference_period"], f) for f in spec["transform_factors"]]
        if row.get("homogeneous") != expected_hom:
            errors.append("homogeneous:" + case["id"])
        base_norm = [e["normalized"] + ":" + e["event"] + ":" + e["state"] + ":" + str(e["held"]) + ":" + e.get("reason", "") for e in expected_base["trace"]]
        for actual in row.get("homogeneous", []):
            normalized = [e["normalized"] + ":" + e["event"] + ":" + e["state"] + ":" + str(e["held"]) + ":" + e.get("reason", "") for e in actual.get("trace", [])]
            if normalized != base_norm:
                errors.append("symmetry:" + case["id"] + ":" + actual.get("factor", "?"))
        controls = row.get("fixed_controls", {})
        for name in spec["fixed_parameter_controls"]:
            expected = independent_trace(case, spec["reference_period"], "2", name)
            if controls.get(name) != expected:
                errors.append("fixed:" + case["id"] + ":" + name)
    # Positive control: an unscaled lease must change a reachable release boundary.
    null_row = by_id.get("null")
    if null_row:
        base_norm = [(e["normalized"], e["event"], e["state"], e["held"], e.get("reason")) for e in null_row["base"]["trace"]]
        lease_norm = [(e["normalized"], e["event"], e["state"], e["held"], e.get("reason")) for e in null_row["fixed_controls"]["lease"]["trace"]]
        if base_norm == lease_norm:
            errors.append("fixed_lease_reachable_witness")
        # Negative control: keeping an already-zero startup delay fixed is observationally unreachable.
        startup_norm = [(e["normalized"], e["event"], e["state"], e["held"], e.get("reason")) for e in null_row["fixed_controls"]["startup_delay"]["trace"]]
        if base_norm != startup_norm:
            errors.append("fixed_zero_startup_unreachable_control")
    return errors


def main(spec_path, raw_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    raw = json.load(open(raw_path, encoding="utf-8"))
    errors = check(spec, raw)
    # Four bounded corruption controls: missing case, omitted trace row, wrong state, false release.
    controls = []
    for mutate in (
        lambda x: x["rows"].pop(),
        lambda x: x["rows"][0]["base"]["trace"].pop(),
        lambda x: x["rows"][1]["base"]["trace"][0].update(state="forged"),
        lambda x: x["rows"][0]["base"].update(released=not x["rows"][0]["base"]["released"]),
    ):
        changed = copy.deepcopy(raw)
        mutate(changed)
        controls.append(bool(check(spec, changed)))
    if not all(controls):
        errors.append("mutation_control")
    result = {"status":"PASS_LOGICAL_TIME_SYMMETRY_SCOPED" if not errors else "FAIL_METHOD", "errors":errors, "mutation_rejections":sum(controls), "mutation_controls":len(controls), "candidate_rows":len(raw.get("rows", []))}
    json.dump(result, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))

