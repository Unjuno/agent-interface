"""Raw-only independent reconstruction; imports neither candidate nor coders."""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent

def raw_annotation(row, penalty):
    expected_row_keys = {"row_id", "pair_id", "blind_code", "goal", "allowed_methods", "segments", "final_outcome"}
    if set(row) != expected_row_keys:
        raise ValueError("raw row contains unknown or arm-revealing fields")
    segments = []
    for segment in row["segments"]:
        if set(segment) != {"method", "operators", "events", "duration_ms", "outcome"}:
            raise ValueError("raw segment schema mismatch")
        if segment["method"] not in row["allowed_methods"]:
            raise ValueError("raw trace selects a disallowed method")
        events = list(segment["events"])
        segments.append({
            "method": segment["method"], "operators": list(segment["operators"]),
            "duration_ms": int(segment["duration_ms"]), "outcome": segment["outcome"],
            "errors": events.count("error"), "switches": events.count("switch"),
            "terminal": "complete" if "complete" in events else ("timeout" if "timeout" in events else "nonterminal"),
        })
    unfinished = row["final_outcome"] == "unfinished"
    return {
        "row_id": row["row_id"], "pair_id": row["pair_id"], "goal": row["goal"],
        "segments": segments, "final_outcome": row["final_outcome"],
        "elapsed_ms": sum(s["duration_ms"] for s in segments),
        "penalty_ms": int(penalty if unfinished else 0),
        "errors": sum(s["errors"] for s in segments),
        "switches": sum(s["switches"] for s in segments),
    }

def validate(traces, arm_key, got):
    errors = []
    if got.get("schema") != "issue6243-t0-successor02-result-v1":
        errors.append("result schema mismatch")
    expected_scenarios = {item["id"] for item in traces["scenarios"]}
    observed = {item.get("id"): item for item in got.get("scenarios", [])}
    if set(observed) != expected_scenarios:
        errors.append("scenario denominator mismatch")
    for scenario in traces["scenarios"]:
        out = observed.get(scenario["id"], {})
        rows = scenario["rows"]
        ids = sorted(row["row_id"] for row in rows)
        if out.get("attempt_count") != len(rows) or out.get("attempt_ids") != ids:
            errors.append(scenario["id"] + ": attempt denominator lost or duplicated")
        pairs = {pair.get("row_id"): pair for pair in out.get("annotation_pairs", [])}
        if set(pairs) != set(ids):
            errors.append(scenario["id"] + ": coder-pair denominator mismatch")
        stats = defaultdict(lambda: {"n": 0, "elapsed_ms": 0, "penalty_ms": 0, "errors": 0, "switches": 0, "correct": 0, "failed": 0, "unfinished": 0})
        methods = defaultdict(lambda: {"segments": 0, "elapsed_ms": 0, "errors": 0, "switches": 0})
        agreement_matches = 0
        for row in rows:
            try:
                expected = raw_annotation(row, traces["unfinished_penalty_ms"])
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(row.get("row_id", "unknown") + ": invalid raw trace: " + str(exc))
                continue
            pair = pairs.get(row["row_id"], {})
            if pair.get("a") != expected or pair.get("b") != expected:
                errors.append(row["row_id"] + ": annotation differs from independent raw reconstruction")
            agreement_matches += int(pair.get("a") == pair.get("b"))
            arm = arm_key[scenario["id"]][row["blind_code"]]
            bucket = stats[arm]
            bucket["n"] += 1
            bucket["elapsed_ms"] += expected["elapsed_ms"]
            bucket["penalty_ms"] += expected["penalty_ms"]
            bucket["errors"] += expected["errors"]
            bucket["switches"] += expected["switches"]
            bucket["correct"] += int(expected["final_outcome"] == "correct")
            bucket["failed"] += int(expected["final_outcome"] == "failed")
            bucket["unfinished"] += int(expected["final_outcome"] == "unfinished")
            for segment in expected["segments"]:
                method = methods[(arm, segment["method"])]
                method["segments"] += 1
                method["elapsed_ms"] += segment["duration_ms"]
                method["errors"] += segment["errors"]
                method["switches"] += segment["switches"]
        expected_arms = {
            arm: {**values, "scored_ms": values["elapsed_ms"] + values["penalty_ms"], "acquisition_ms": scenario["acquisition_ms"][arm]}
            for arm, values in sorted(stats.items())
        }
        if out.get("arms") != expected_arms:
            errors.append(scenario["id"] + ": arm totals/costs differ from raw attempts")
        expected_methods = [
            {"arm": arm, "method": method, **values, "mean_elapsed_ms": values["elapsed_ms"] / values["segments"]}
            for (arm, method), values in sorted(methods.items())
        ]
        if out.get("method_summary") != expected_methods:
            errors.append(scenario["id"] + ": method-conditioned accounting differs from raw segments")
        agreement = agreement_matches / len(rows)
        if out.get("coder_agreement") != agreement or agreement < traces["agreement_threshold"]:
            errors.append(scenario["id"] + ": coder agreement below threshold or misstated")
        if out.get("all_attempts_preserved") is not True:
            errors.append(scenario["id"] + ": all-attempt preservation flag false")
    mix = observed.get("shortcut_mixture", {})
    expected_horizons = {
        str(repeats): {
            arm: mix.get("arms", {}).get(arm, {}).get("acquisition_ms", -1)
                 + repeats * mix.get("arms", {}).get(arm, {}).get("scored_ms", -1)
            for arm in ("H", "A")
        }
        for repeats in traces["horizon_repeats"]
    }
    if mix.get("horizon_sensitivity") != expected_horizons:
        errors.append("acquisition-inclusive horizon totals mismatch")
    null = observed.get("equal_method_null", {}).get("arms", {})
    if null.get("H", {}).get("scored_ms") != null.get("A", {}).get("scored_ms"):
        errors.append("equal-method null is not exactly equal")
    null_raw = next(item for item in traces["scenarios"] if item["id"] == "equal_method_null")
    null_by_pair = defaultdict(dict)
    for row in null_raw["rows"]:
        arm = arm_key["equal_method_null"][row["blind_code"]]
        try:
            null_by_pair[row["pair_id"]][arm] = raw_annotation(row, traces["unfinished_penalty_ms"])
        except (KeyError, TypeError, ValueError):
            errors.append(row.get("row_id", "unknown") + ": invalid equal-null raw trace")
    if any(
        {key: value for key, value in pair.get("H", {}).items() if key != "row_id"}
        != {key: value for key, value in pair.get("A", {}).items() if key != "row_id"}
        for pair in null_by_pair.values()
    ):
        errors.append("equal-method null differs within a paired task")
    mix_methods = observed.get("shortcut_mixture", {}).get("method_summary", [])
    means = {(item["arm"], item["method"]): item["mean_elapsed_ms"] for item in mix_methods}
    if any(means.get(("H", method)) != means.get(("A", method)) for method in ("ordinary", "shortcut")):
        errors.append("same-method synthetic timing differs between arms")
    if mix.get("horizon_sensitivity", {}).get("1", {}).get("H", 0) <= mix.get("horizon_sensitivity", {}).get("1", {}).get("A", 0):
        errors.append("predeclared one-repeat acquisition ordering did not reverse")
    for repeats in ("4", "10"):
        if mix.get("horizon_sensitivity", {}).get(repeats, {}).get("H", 10**30) >= mix.get("horizon_sensitivity", {}).get(repeats, {}).get("A", -1):
            errors.append("predeclared repeat-horizon ordering not recovered at " + repeats)
    switches = observed.get("switch_and_failure", {}).get("arms", {}).get("H", {})
    switch_raw = next(item for item in traces["scenarios"] if item["id"] == "switch_and_failure")
    failed_segments = sum(segment["outcome"] == "failed" for row in switch_raw["rows"] for segment in row["segments"])
    if failed_segments != 2 or switches.get("switches") != 2 or switches.get("errors") != 2:
        errors.append("failed segment/switch/event accounting mismatch")
    unfinished = observed.get("unfinished_attempts", {}).get("arms", {}).get("H", {})
    if unfinished.get("unfinished") != 2 or unfinished.get("penalty_ms") != 2 * traces["unfinished_penalty_ms"]:
        errors.append("unfinished attempts or fixed penalties omitted")
    return errors

def mutation_results(traces, arm_key, result):
    import copy
    mutations = {}

    dropped = copy.deepcopy(result)
    section = next(item for item in dropped["scenarios"] if item["id"] == "switch_and_failure")
    section["attempt_ids"].remove("switch01-H")
    section["annotation_pairs"] = [pair for pair in section["annotation_pairs"] if pair["row_id"] != "switch01-H"]
    section["attempt_count"] -= 1
    mutations["drop_failed_attempt"] = bool(validate(traces, arm_key, dropped))

    no_charge = copy.deepcopy(result)
    section = next(item for item in no_charge["scenarios"] if item["id"] == "shortcut_mixture")
    section["horizon_sensitivity"]["4"]["H"] -= section["arms"]["H"]["acquisition_ms"]
    mutations["omit_acquisition_cost"] = bool(validate(traces, arm_key, no_charge))

    forbidden = copy.deepcopy(result)
    section = next(item for item in forbidden["scenarios"] if item["id"] == "equal_method_null")
    pair = next(pair for pair in section["annotation_pairs"] if pair["row_id"] == "null01-H")
    pair["a"]["segments"][0]["method"] = "shortcut"
    mutations["use_prohibited_shortcut"] = bool(validate(traces, arm_key, forbidden))

    exposed = copy.deepcopy(traces)
    exposed["scenarios"][1]["rows"][0]["arm"] = "H"
    mutations["arm_visible_to_coder"] = bool(validate(exposed, arm_key, result))
    return mutations

if __name__ == "__main__":
    traces = json.loads((ROOT / "traces.json").read_text())
    key = json.loads((ROOT / "key.json").read_text())
    result = json.loads((ROOT / "candidate_result.json").read_text())
    errors = validate(traces, key, result)
    mutations = mutation_results(traces, key, result)
    for name, rejected in mutations.items():
        if not rejected:
            errors.append("mutation escaped: " + name)
    audit = {
        "decision": "METHOD_PASS_SCOPED" if not errors else "FAIL_AUDIT_GATE",
        "attempts": sum(len(item["rows"]) for item in traces["scenarios"]),
        "scenario_count": len(traces["scenarios"]),
        "mutation_controls_rejected": sum(mutations.values()),
        "mutation_controls_total": len(mutations),
        "mutations": mutations,
        "errors": errors,
    }
    (ROOT / "audit_result.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))
    sys.exit(bool(errors))
