#!/usr/bin/env python3
"""Independent raw-only oracle for the Issue #6617 finite event trace."""
import argparse
import copy
import json
from pathlib import Path


ARMS = {"final_only", "naive_provisional", "version_bound_read_only"}
SAFE = {"final_only", "version_bound_read_only"}
ORACLE = {
    "C01": {"intent":"send:alice","turn":"T1","version":2,"principal":"P1","act":True,"provisional":"send:alice"},
    "C02": {"intent":None,"turn":"T1","version":3,"principal":"P1","act":False,"provisional":"send:alice"},
    "C03": {"intent":"send:bob","turn":"T1","version":3,"principal":"P1","act":True,"provisional":"send:alice"},
    "C04": {"intent":None,"turn":"T1","version":2,"principal":"P1","act":False,"provisional":"delete:folder"},
    "C05": {"intent":"archive:bob","turn":"T2","version":1,"principal":"P2","act":True,"provisional":"send:alice"},
    "C06": {"intent":"archive:bob","turn":"T1","version":3,"principal":"P1","act":True,"provisional":"send:alice"},
    "C07": {"intent":None,"turn":"T1","version":2,"principal":"P1","act":True,"provisional":"send:alice"},
    "C08": {"intent":"send:alice","turn":"T1","version":2,"principal":"P1","act":True,"provisional":"send:alice"},
    "C09": {"intent":"send:alice","turn":"T1","version":2,"principal":"P1","act":True,"provisional":"send:alice"},
    "C10": {"intent":None,"turn":None,"version":None,"principal":None,"act":False,"provisional":None},
}


def reject(condition, message, errors):
    if condition:
        errors.append(message)


def audit(raw):
    errors = []
    reject(raw.get("schema") != "revision-timed-cutover-raw-v1", "raw schema mismatch", errors)
    rows = raw.get("rows")
    reject(not isinstance(rows, list), "rows is not a list", errors)
    if not isinstance(rows, list):
        return ["rows is not a list"], {}
    indexed = {}
    for row in rows:
        if not isinstance(row, dict):
            errors.append("row is not an object")
            continue
        key = (row.get("scenario_id"), row.get("arm"))
        if key in indexed:
            errors.append(f"duplicate row {key}")
        indexed[key] = row
    expected_keys = {(case, arm) for case in ORACLE for arm in ARMS}
    reject(set(indexed) != expected_keys, "scenario/arm roster mismatch", errors)
    metrics = {}
    for (case_id, arm), row in indexed.items():
        oracle = ORACLE.get(case_id)
        if oracle is None or arm not in ARMS:
            errors.append(f"unknown scenario or arm: {(case_id, arm)}")
            continue
        events = row.get("events")
        if not isinstance(events, list) or any(not isinstance(e, dict) for e in events):
            errors.append(f"malformed events: {(case_id, arm)}")
            continue
        inputs = [e for e in events if e.get("kind") == "consequential_input"]
        effects = [e for e in events if e.get("kind") == "effect_verified"]
        unknown = [e for e in events if e.get("kind") == "effect_unknown"]
        retries = [e for e in events if e.get("kind") == "retry" and e.get("allowed") is True]
        inverses = [e for e in events if e.get("kind") == "blind_inverse" and e.get("allowed") is True]
        dispositions = [e for e in events if e.get("kind") == "effect_disposition"]
        unsafe = [e for e in inputs if e.get("provisional") is True or e.get("authenticated") is not True or e.get("committed") is not True]
        metrics.setdefault("input_count_by_arm", {}).setdefault(arm, 0)
        metrics["input_count_by_arm"][arm] += len(inputs)
        metrics.setdefault("unsafe_provisional_input_count_by_arm", {}).setdefault(arm, 0)
        metrics["unsafe_provisional_input_count_by_arm"][arm] += len(unsafe)
        metrics.setdefault("verified_effect_count_by_arm", {}).setdefault(arm, 0)
        metrics["verified_effect_count_by_arm"][arm] += len(effects)
        expected_intent = oracle["intent"] if arm in SAFE else oracle["provisional"]
        should_input = (expected_intent is not None and
                        (arm not in SAFE or oracle["act"]))
        reject(len(inputs) != int(should_input), f"input count mismatch: {(case_id, arm)}", errors)
        for item in inputs:
            reject(item.get("intent") != expected_intent, f"wrong intent: {(case_id, arm)}", errors)
            if arm in SAFE:
                reject(item.get("turn") != oracle["turn"], f"source turn mismatch: {(case_id, arm)}", errors)
                reject(item.get("version") != oracle["version"], f"source version mismatch: {(case_id, arm)}", errors)
                reject(item.get("principal") != oracle["principal"], f"principal mismatch: {(case_id, arm)}", errors)
                reject(item.get("authenticated") is not True or item.get("committed") is not True,
                       f"uncommitted/unauthenticated safe-arm input: {(case_id, arm)}", errors)
                reject(item.get("provisional") is not False, f"provisional safe-arm input: {(case_id, arm)}", errors)
            else:
                reject(item.get("authenticated") is not False or item.get("committed") is not False or item.get("provisional") is not True,
                       f"naive comparator lost its provisional label: {(case_id, arm)}", errors)
        for effect in effects:
            reject(not inputs, f"effect without physical input: {(case_id, arm)}", errors)
            reject(effect.get("verified") is not True, f"unverified effect tagged verified: {(case_id, arm)}", errors)
            reject(effect.get("intent") != expected_intent, f"effect intent mismatch: {(case_id, arm)}", errors)
        if case_id == "C01" and arm == "version_bound_read_only":
            finals = [e for e in events if e.get("kind") == "final"]
            if effects and finals:
                metrics["version_bound_stable_latency_ticks"] = effects[0]["time"] - finals[0]["time"]
        if case_id == "C01" and arm == "final_only":
            finals = [e for e in events if e.get("kind") == "final"]
            if effects and finals:
                metrics["final_only_stable_latency_ticks"] = effects[0]["time"] - finals[0]["time"]
        if case_id == "C06" and arm == "version_bound_read_only":
            stale_actions = [e for e in inputs if e.get("intent") == "send:alice"]
            reject(bool(stale_actions), "stale completion revived invalidated epoch", errors)
            drops = [e for e in events if e.get("kind") == "prepared_candidate_disposition" and e.get("disposition") == "discarded_version_or_principal_mismatch"]
            reject(not drops, "changed epoch has no explicit discard receipt", errors)
        if arm == "version_bound_read_only" and case_id in {"C02", "C03", "C04", "C05", "C06"}:
            drops = [e for e in events if e.get("kind") == "prepared_candidate_disposition" and e.get("disposition", "").startswith("discarded_")]
            reject(not drops, f"invalidated/non-effectful preparation lacks discard receipt: {(case_id, arm)}", errors)
        if case_id == "C07" and arm in SAFE:
            releases = [e for e in events if e.get("kind") == "release_verified" and e.get("verified") is True]
            reject(not releases, f"pre-input stop did not retain verified release: {(case_id, arm)}", errors)
        if case_id == "C08":
            reject(bool(unknown) != should_input, f"pending-unknown classification mismatch: {(case_id, arm)}", errors)
            reject(bool(retries) or bool(inverses), f"unknown effect permits retry or blind inverse: {(case_id, arm)}", errors)
        if case_id == "C09" and should_input:
            already = [e for e in dispositions if e.get("status") == "already_occurred"]
            reject(not already, f"verified late-stop outcome not typed already-occurred: {(case_id, arm)}", errors)
            reject(any(e.get("automatic_undo") is not False or e.get("fresh_remedy_required") is not True for e in already),
                   f"late stop treated as automatic undo: {(case_id, arm)}", errors)
        if case_id == "C10":
            rel = [e for e in events if e.get("kind") == "release_verified"]
            pc = [e for e in events if e.get("kind") == "planner_completion"]
            reject(len(rel) != 1 or rel[0].get("time", 999) >= 20, f"urgent release not independent/early: {(case_id, arm)}", errors)
            reject(len(pc) != 1 or not rel or rel[0].get("time", 999) >= pc[0].get("time", -1), f"release waited for planner: {(case_id, arm)}", errors)
    a = metrics.get("final_only_stable_latency_ticks")
    b = metrics.get("version_bound_stable_latency_ticks")
    reject(not isinstance(a, int) or not isinstance(b, int) or b >= a, "stable scripted route has no latency improvement", errors)
    metrics["stable_latency_saving_ticks"] = a - b if isinstance(a, int) and isinstance(b, int) else None
    unsafe_counts = metrics.get("unsafe_provisional_input_count_by_arm", {})
    reject(unsafe_counts.get("naive_provisional") != 9, "unsafe naive comparator inputs were not all independently detected", errors)
    reject(any(unsafe_counts.get(arm) != 0 for arm in SAFE), "safe arm admitted a provisional/unauthenticated/uncommitted input", errors)
    return errors, metrics


def mutation_controls(raw):
    cases = {}
    def find(case, arm):
        return next(r for r in cases["rows"] if r["scenario_id"] == case and r["arm"] == arm)
    names = ("old_epoch", "partial_as_final", "speaker_merge", "cancel_as_undo")
    results = {}
    for name in names:
        mutant = copy.deepcopy(raw)
        cases["rows"] = mutant["rows"]
        if name == "old_epoch":
            inp = next(e for e in find("C03", "version_bound_read_only")["events"] if e["kind"] == "consequential_input")
            inp["version"] = 1
        elif name == "partial_as_final":
            inp = next(e for e in find("C02", "version_bound_read_only")["events"] if e["kind"] == "final")
            inp["speech_act"] = "request"
            find("C02", "version_bound_read_only")["events"].append({"kind":"consequential_input","time":11,"turn":"T1","version":1,"principal":"P1","intent":"send:alice","authenticated":True,"committed":True,"provisional":False})
        elif name == "speaker_merge":
            inp = next(e for e in find("C05", "version_bound_read_only")["events"] if e["kind"] == "consequential_input")
            inp.update({"principal":"P1","turn":"T1","version":2,"intent":"send:alice"})
        else:
            find("C08", "version_bound_read_only")["events"].append({"kind":"blind_inverse","time":99,"allowed":True})
        errs, _ = audit(mutant)
        results[name] = {"rejected": bool(errs), "error_count": len(errs)}
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = json.loads(Path(a.raw).read_text(encoding="utf-8"))
    errors, metrics = audit(raw)
    controls = mutation_controls(raw)
    result = {"schema":"revision-timed-cutover-audit-v1","passed":not errors and all(x["rejected"] for x in controls.values()),
              "disposition":"PASS_METHOD_SCOPED" if not errors and all(x["rejected"] for x in controls.values()) else "FAIL_METHOD",
              "errors":errors,"metrics":metrics,"mutation_controls":controls,"raw_rows":len(raw.get("rows",[])),
              "limits":"deterministic logical-time model only; no speech/audio, human intention, GUI, model, physical input, or real latency evidence"}
    Path(a.out).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({"passed":result["passed"],"disposition":result["disposition"],"errors":len(errors),"mutations_rejected":sum(v["rejected"] for v in controls.values())}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
