"""Independent raw-only replay and truth-side scoring; imports no candidate code."""
import argparse
import json
from pathlib import Path


POLICY_ORDER = ["fixed_period", "prediction_triggered", "bounded_hold", "no_continuation"]
PERIOD = 4
CHUNK_LIMIT = 8
THRESHOLD = 2.0


def expected_trace(case, policy):
    states = case["observations"]
    target = case["intended_identity"]
    x = float(case["initial_agent_x"])
    direction = 0
    ended = False
    capture_events = 0
    chunk_origin = 0
    previous_capture = None
    current_capture = None
    records = []
    for tick, obs in enumerate(states):
        why = None
        invalid_now = (obs["identity"] != target or obs["focus_valid"] is not True
                       or obs["lease_valid"] is not True or obs["capture_x"] is None)
        if invalid_now:
            direction, ended, why = 0, True, "invalidation_release"
        elif not ended:
            if capture_events == 0:
                why = "initial"
            elif policy == "fixed_period" and tick % PERIOD == 0:
                why = "fixed_period"
            elif policy == "bounded_hold" and tick - chunk_origin >= CHUNK_LIMIT:
                why = "max_chunk"
            elif policy == "prediction_triggered":
                if tick - chunk_origin >= CHUNK_LIMIT:
                    why = "max_chunk"
                elif current_capture is not None:
                    if previous_capture is None:
                        forecast = current_capture[1]
                    else:
                        elapsed = current_capture[0] - previous_capture[0]
                        slope = ((current_capture[1] - previous_capture[1]) / elapsed
                                 if elapsed > 0 else 0.0)
                        forecast = current_capture[1] + slope * (tick - current_capture[0])
                    if obs["probe_x"] is None or abs(obs["probe_x"] - forecast) > THRESHOLD:
                        why = "prediction_error"
            elif policy == "no_continuation" and tick > 0:
                direction, ended, why = 0, True, "bounded_baseline_release"

            if why not in (None, "invalidation_release", "bounded_baseline_release"):
                previous_capture = current_capture
                current_capture = (tick, float(obs["capture_x"]))
                direction = (current_capture[1] > x) - (current_capture[1] < x)
                chunk_origin = tick
                capture_events += 1

        before = x
        x += direction
        records.append({"tick": tick,
                        "capture": why not in (None, "invalidation_release", "bounded_baseline_release"),
                        "trigger": why, "command": direction,
                        "agent_before": round(before, 4), "agent_after": round(x, 4),
                        "identity": obs["identity"], "focus_valid": obs["focus_valid"],
                        "lease_valid": obs["lease_valid"]})
    return records, capture_events


def evaluate(case, truth_case, trace):
    truth = truth_case["states"]
    intended = truth_case["intended_identity"]
    best = None
    for observed, target in zip(trace, truth):
        if target["target_identity"] == intended and target["target_x"] is not None:
            distance = abs(observed["agent_after"] - target["target_x"])
            best = distance if best is None else min(best, distance)
    useful = best is not None and best <= 1.0
    invalid_ticks = [i for i, obs in enumerate(case["observations"])
                     if obs["identity"] != case["intended_identity"]
                     or not obs["focus_valid"] or not obs["lease_valid"]
                     or obs["capture_x"] is None]
    false_continue = sum(1 for i in invalid_ticks if trace[i]["command"] != 0)
    occupancy = sum(1 for row in trace if row["command"] != 0)
    return {"useful_effect": useful, "best_target_distance": round(best, 4) if best is not None else None,
            "invalid_ticks": invalid_ticks, "false_continue_ticks": false_continue,
            "occupancy_ticks": occupancy,
            "release_lag_ticks": [0 if trace[i]["command"] == 0 else None for i in invalid_ticks]}


def audit(input_path, truth_path, raw_path):
    visible = json.loads(Path(input_path).read_text(encoding="utf-8"))
    oracle = json.loads(Path(truth_path).read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in Path(raw_path).read_text(encoding="utf-8").splitlines() if line]
    expected_count = len(visible["cases"]) * len(POLICY_ORDER)
    errors = []
    if len(raw) != expected_count:
        errors.append("row_count")
    truth_by_case = {c["case_id"]: c for c in oracle["cases"]}
    visible_by_case = {c["case_id"]: c for c in visible["cases"]}
    seen = set()
    results = []
    for row in raw:
        key = (row.get("case_id"), row.get("policy"))
        if key in seen or key[0] not in visible_by_case or key[1] not in POLICY_ORDER:
            errors.append("row_identity_or_duplicate")
            continue
        seen.add(key)
        case = visible_by_case[key[0]]
        expected, captures = expected_trace(case, key[1])
        if row.get("trace") != expected:
            errors.append("trajectory_mismatch:" + key[0] + ":" + key[1])
        score = evaluate(case, truth_by_case[key[0]], expected)
        occupancy = sum(1 for item in expected if item["command"] != 0)
        proxy = captures * 10 + len(case["observations"])
        if row.get("capture_count") != captures or row.get("occupancy_ticks") != occupancy:
            errors.append("counter_mismatch:" + key[0] + ":" + key[1])
        if occupancy > 40:
            errors.append("occupancy_budget:" + key[0] + ":" + key[1])
        if score["false_continue_ticks"]:
            errors.append("continued_after_invalidation:" + key[0] + ":" + key[1])
        results.append({"case_id": key[0], "policy": key[1], "captures": captures,
                        "cpu_proxy": proxy, **score})
    if seen != {(c["case_id"], p) for c in visible["cases"] for p in POLICY_ORDER}:
        errors.append("inventory_incomplete")
    by_case = {}
    for item in results:
        by_case.setdefault(item["case_id"], {})[item["policy"]] = item
    controls = {}
    for case_id in ("perfect_tracker_positive", "stale_tracker_negative"):
        b = by_case.get(case_id, {}).get("prediction_triggered", {})
        f = by_case.get(case_id, {}).get("fixed_period", {})
        controls[case_id] = {"predictive_captures": b.get("captures"),
                             "fixed_captures": f.get("captures"),
                             "predictive_effect": b.get("useful_effect"),
                             "fixed_effect": f.get("useful_effect")}
    if not controls["perfect_tracker_positive"]["predictive_captures"] < controls["perfect_tracker_positive"]["fixed_captures"]:
        errors.append("perfect_tracker_control")
    if not controls["stale_tracker_negative"]["predictive_captures"] > controls["perfect_tracker_positive"]["predictive_captures"]:
        errors.append("stale_tracker_control")
    summary = {}
    for policy in POLICY_ORDER:
        group = [v[policy] for v in by_case.values()]
        summary[policy] = {"useful_effect_cases": sum(bool(x["useful_effect"]) for x in group),
                           "capture_total": sum(x["captures"] for x in group),
                           "occupancy_total": sum(x["occupancy_ticks"] for x in group),
                           "false_continue_ticks": sum(x["false_continue_ticks"] for x in group)}
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "rows": len(raw), "errors": errors, "controls": controls,
            "summary": summary, "details": results}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--truth", required=True)
    p.add_argument("--raw", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    result = audit(a.input, a.truth, a.raw)
    Path(a.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": result["rows"],
                      "errors": result["errors"]}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
