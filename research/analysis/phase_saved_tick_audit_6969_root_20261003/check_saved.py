"""Supplementary saved-only oracle; never imports or executes study code."""
import argparse
import copy
import hashlib
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def reconstruct(case):
    """Advance each integer tick, admitting events in capture/delivery/decision order.

    Capture remains a snapshot; a timely decision may yield an effect after cue
    expiry. This deliberately models the frozen contract, not real GUI authority.
    """
    cue = case["opportunity"]
    stages = dict.fromkeys(("delivery", "decision", "effect", "safe_stop"))
    sampled = []
    pending = {}
    for tick in range(case["observation_horizon_ms"] + 1):
        visible = (cue is not None and case["clock_synchronized"]
                   and cue["onset_ms"] <= tick <= cue["expiry_ms"])
        if visible and tick in case["capture_schedule_ms"]:
            sampled.append(tick)
            if len(sampled) == 1:
                pending["delivery"] = tick + case["delivery_latency_ms"]
        if pending.get("delivery") == tick:
            stages["delivery"] = tick
            if visible:
                pending["decision"] = tick + case["decision_latency_ms"]
        if pending.get("decision") == tick:
            stages["decision"] = tick
            if visible:
                if case["safe_stop"]:
                    stages["safe_stop"] = tick
                elif case["effect_enabled"]:
                    pending["effect"] = tick + case["effect_latency_ms"]
        if pending.get("effect") == tick:
            stages["effect"] = tick
    if cue is None:
        verdict = ("NOT_APPLICABLE", "no_exogenous_opportunity")
    elif not case["clock_synchronized"]:
        verdict = ("UNKNOWN", "clock_unsynced")
    elif (case["observation_horizon_ms"] < cue["expiry_ms"]
          and stages["effect"] is None and stages["safe_stop"] is None):
        verdict = ("UNKNOWN", "right_censored")
    elif not sampled:
        verdict = ("not_acquired", "no_capture_in_closed_interval")
    elif stages["delivery"] is None or stages["delivery"] > cue["expiry_ms"]:
        verdict = ("acquired_not_delivered", "no_timely_delivery_observed")
    elif stages["decision"] is None or stages["decision"] > cue["expiry_ms"]:
        verdict = ("delivered_no_decision", "no_timely_decision_observed")
    elif stages["safe_stop"] is not None:
        verdict = ("decision_no_effect", "safe_stop")
    elif stages["effect"] is not None:
        verdict = ("eligible_effect_in_model", "simulated_effect_observed")
    else:
        verdict = ("decision_no_effect", "no_simulated_effect_observed")
    return dict(case_id=case["case_id"], opportunity=cue,
                capture_schedule_ms=case["capture_schedule_ms"],
                observation_horizon_ms=case["observation_horizon_ms"],
                sampled_capture_ms=sampled, stages_ms=stages,
                boundary=verdict[0], reason=verdict[1],
                simulated_effect_token=("simulated:" + case["case_id"]
                                        if stages["effect"] is not None else None))


def leaves(value, path=()):
    if type(value) is dict:
        for key in sorted(value):
            yield from leaves(value[key], path + (key,))
    elif type(value) is list:
        for index, child in enumerate(value):
            yield from leaves(child, path + (index,))
    else:
        yield path, value


def changed(value):
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return value + "!corrupt"
    if type(value) is bool:
        return not value
    if value is None:
        return "!corrupt-null"
    raise ValueError("unexpected scalar type")


def run(plan, study):
    for relative, expected_hash in plan["input_sha256"].items():
        actual = hashlib.sha256((study / relative).read_bytes()).hexdigest()
        if actual != expected_hash:
            raise ValueError("source identity mismatch: " + relative)
    fixture = json.loads((study / "fixture.json").read_bytes())
    raw = json.loads((study / "formal_02/candidate/raw.json").read_bytes())
    wanted = {"schema": "derived-capture-raw-v1", "fixture_id": fixture["fixture_id"],
              "authority_events": 0, "live_effect_events": 0,
              "rows": [reconstruct(case) for case in fixture["cases"]]}
    baseline_match = canonical(raw) == canonical(wanted)
    controls = []
    for path, original in leaves(raw):
        mutant = copy.deepcopy(raw)
        parent = mutant
        for part in path[:-1]:
            parent = parent[part]
        parent[path[-1]] = replacement = changed(original)
        controls.append({"path": list(path), "original": original,
                         "replacement": replacement,
                         "effective": canonical(mutant) != canonical(raw),
                         "rejected": canonical(mutant) != canonical(wanted)})
    structural = []
    for name in ("drop-last", "duplicate-first", "reverse-rows", "extra-field"):
        mutant = copy.deepcopy(raw)
        if name == "drop-last":
            mutant["rows"].pop()
        elif name == "duplicate-first":
            mutant["rows"][1] = copy.deepcopy(mutant["rows"][0])
        elif name == "reverse-rows":
            mutant["rows"].reverse()
        else:
            mutant["unexpected"] = True
        structural.append({"name": name, "effective": canonical(mutant) != canonical(raw),
                           "rejected": canonical(mutant) != canonical(wanted)})
    aliases = []
    for path, original in leaves(raw):
        if type(original) is int and original in (0, 1):
            mutant = copy.deepcopy(raw)
            parent = mutant
            for part in path[:-1]:
                parent = parent[part]
            parent[path[-1]] = bool(original)
            aliases.append({"path": list(path), "python_equality_alias": mutant == raw,
                            "effective": canonical(mutant) != canonical(raw),
                            "rejected": canonical(mutant) != canonical(wanted)})
    all_controls = controls + structural + aliases
    ok = (baseline_match and len(wanted["rows"]) == 147
          and all(c["effective"] and c["rejected"] for c in all_controls))
    return {"disposition": "PASS_SAVED_FINITE_AUDIT" if ok else "FAIL_SAVED_FINITE_AUDIT",
            "rows": len(wanted["rows"]), "baseline_exact_match": baseline_match,
            "boundary_counts": dict(Counter(row["boundary"] for row in wanted["rows"])),
            "scalar_controls": controls, "structural_controls": structural,
            "type_alias_controls": aliases, "total_controls": len(all_controls),
            "effective_rejected": sum(c["effective"] and c["rejected"] for c in all_controls),
            "python": platform.python_version(), "platform": platform.platform(),
            "candidate_invocations": 0, "original_auditor_invocations": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    plan = json.loads(args.plan.read_bytes())
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != plan["checker_sha256"]:
        raise ValueError("checker differs from prospective plan")
    result = run(plan, args.study)
    result.update(started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat())
    with args.out.open("x") as target:
        json.dump(result, target, sort_keys=True, indent=2)
        target.write("\n")
    print(result["disposition"], "rows=", result["rows"], "controls=", result["total_controls"])
    raise SystemExit(0 if result["disposition"].startswith("PASS") else 1)
