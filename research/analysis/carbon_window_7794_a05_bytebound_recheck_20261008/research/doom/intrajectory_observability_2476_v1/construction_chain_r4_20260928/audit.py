import argparse
import copy
import hashlib
import json
from pathlib import Path


POLICIES = ("PER_HOP_ONLY", "PER_HOP_PLUS_GLOBAL_12PX")
EXPECTED = {
    "exact_three_hops": {p: None for p in POLICIES},
    "cumulative_drift_exactly_12": {p: None for p in POLICIES},
    "repeated_8px_hop_residual_crosses_global_at_hop2": {
        "PER_HOP_ONLY": None, "PER_HOP_PLUS_GLOBAL_12PX": (2, "GLOBAL_DRIFT_BOUND")},
    "cumulative_drift_crosses_at_13px_hop3": {
        "PER_HOP_ONLY": None, "PER_HOP_PLUS_GLOBAL_12PX": (3, "GLOBAL_DRIFT_BOUND")},
    "abrupt_translation_at_hop2": {p: (2, "LOCAL_CORRIDOR_MISS") for p in POLICIES},
    "true_target_disappearance_at_hop2": {p: (2, "OBSERVATION_NOT_FOUND") for p in POLICIES},
    "score_below_gate_at_hop3": {p: (3, "CURRENT_MATCH_GATE") for p in POLICIES},
    "stale_hop_age_at_hop2": {p: (2, "OBSERVATION_AGE") for p in POLICIES},
    "geometry_change_at_hop3": {p: (3, "CURRENT_GEOMETRY") for p in POLICIES},
    "frame_sequence_gap_at_hop2": {p: (2, "FRAME_SEQUENCE") for p in POLICIES},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def row_emission_errors(row):
    if "physical_input_emitted" not in row:
        return ["physical_input_emitted_missing"]
    if row["physical_input_emitted"] is not False:
        return ["physical_input_emitted_not_false"]
    return []


def expected_observations(cases):
    by_id = {}
    initial = cases["initial"]
    template = cases["steps_template"]
    for ci, spec in enumerate(cases["cases"]):
        prev_seq, prev_time = initial["frame_seq"], initial["captured_ns"]
        prev_x, prev_y = initial["center_x_px"], initial["center_y_px"]
        steps = []
        for n, residual in enumerate(spec["residuals_px"], 1):
            override = spec.get("step_overrides", {}).get(str(n), {})
            ds = override.get("frame_seq_delta", template["frame_seq_delta"])
            age = override.get("age_ns", template["age_ns"])
            x = override.get("center_x_px", prev_x + 8 + residual)
            y = override.get("center_y_px", prev_y)
            step = {
                "frame_seq": prev_seq + ds,
                "captured_ns": prev_time + age,
                "frame_sha256": "%064x" % (n + ci * 4 + 1),
                "observed_center_px": [x, y],
            }
            steps.append(step)
            prev_seq, prev_time = step["frame_seq"], step["captured_ns"]
            if isinstance(x, int):
                prev_x = x
            if isinstance(y, int):
                prev_y = y
        by_id[spec["id"]] = steps
    return by_id


def validate(raw, cases, freeze):
    errors = []
    if raw.get("allocation") != freeze["allocation"]:
        errors.append("allocation_mismatch")
    if raw.get("cases_sha256") != freeze["source_sha256"]["cases.json"]:
        errors.append("case_hash_mismatch")
    if raw.get("source_sha256") != freeze["source_sha256"]:
        errors.append("source_hash_map_mismatch")
    if raw.get("case_count") != len(cases["cases"]) or raw.get("policy_count") != 2:
        errors.append("top_level_counts_mismatch")
    if raw.get("scheduled_hops_per_policy") != 3 or raw.get("physical_input_emissions") != 0:
        errors.append("top_level_execution_summary_mismatch")

    expected_ids = [c["id"] for c in cases["cases"]]
    expected_keys = [(case_id, policy) for case_id in expected_ids for policy in POLICIES]
    runs = raw.get("runs")
    if not isinstance(runs, list):
        return errors + ["runs_not_list"]
    actual_keys = [(r.get("case_id"), r.get("policy")) for r in runs if isinstance(r, dict)]
    if actual_keys != expected_keys:
        errors.append("run_count_or_order_mismatch")
    observation_map = expected_observations(cases)
    if not isinstance(raw.get("physical_input_emissions"), int):
        errors.append("emission_count_not_integer")

    for run in runs:
        if not isinstance(run, dict):
            errors.append("run_not_object")
            continue
        case_id, policy = run.get("case_id"), run.get("policy")
        if case_id not in EXPECTED or policy not in POLICIES:
            errors.append("unknown_run_key")
            continue
        stop = EXPECTED[case_id][policy]
        stop_step, stop_reason = stop if stop is not None else (None, None)
        if run.get("stopped_at_step") != stop_step:
            errors.append("stop_step_mismatch:" + case_id + ":" + policy)
        rows = run.get("rows")
        if not isinstance(rows, list) or len(rows) != 3:
            errors.append("scheduled_row_count_mismatch:" + case_id + ":" + policy)
            continue
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict):
                errors.append("row_not_object")
                continue
            errors.extend(case_id + ":" + policy + ":" + e for e in row_emission_errors(row))
            if row.get("step") != index:
                errors.append("step_identity_mismatch")
            if index < (stop_step or 4):
                if row.get("state") != "TRACKED" or row.get("reason") != "TRACKED":
                    errors.append("expected_track_mismatch:" + case_id + ":" + policy)
            elif stop_step is not None and index == stop_step:
                if row.get("state") != "ABSTAIN" or row.get("reason") != stop_reason:
                    errors.append("expected_stop_mismatch:" + case_id + ":" + policy)
            else:
                if (row.get("state") != "NOT_REACHED_AFTER_STOP"
                        or row.get("reason") != "PRIOR_STOP"):
                    errors.append("suffix_not_marked_unreached:" + case_id + ":" + policy)
            if stop_step is None or index <= stop_step:
                obs = observation_map[case_id][index - 1]
                for field in ("frame_seq", "captured_ns", "frame_sha256", "observed_center_px"):
                    if row.get(field) != obs[field]:
                        errors.append("raw_observation_mismatch:" + case_id + ":" + policy + ":" + field)
    if len(runs) == 20 and sum(len(r.get("rows", [])) for r in runs if isinstance(r, dict)) != 60:
        errors.append("scheduled_row_total_mismatch")
    return errors


def effective_controls(raw, cases, freeze):
    controls = {}
    variants = {}
    missing = copy.deepcopy(raw)
    del missing["runs"][2]["rows"][2]["physical_input_emitted"]
    variants["missing_suffix_emission_flag"] = missing
    true_value = copy.deepcopy(raw)
    true_value["runs"][2]["rows"][2]["physical_input_emitted"] = True
    variants["true_suffix_emission_flag"] = true_value
    missing_row = copy.deepcopy(raw)
    missing_row["runs"][0]["rows"].pop()
    variants["missing_scheduled_row"] = missing_row
    reordered = copy.deepcopy(raw)
    reordered["runs"].reverse()
    variants["reordered_runs"] = reordered
    for name, variant in variants.items():
        controls[name] = bool(validate(variant, cases, freeze))
    return controls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    src = args.source.resolve()
    freeze = json.loads((src / "FREEZE.json").read_text())
    for name, expected in freeze["source_sha256"].items():
        if sha((src / name).read_bytes()) != expected:
            raise SystemExit("STOP_SOURCE_HASH_MISMATCH:" + name)
    case_bytes = (src / "cases.json").read_bytes()
    cases = json.loads(case_bytes)
    raw_bytes = args.raw.resolve().read_bytes()
    raw = json.loads(raw_bytes)
    errors = validate(raw, cases, freeze)
    controls = effective_controls(raw, cases, freeze)
    if not all(controls.values()):
        errors.append("corruption_control_not_rejected")
    result = {
        "allocation": freeze["allocation"],
        "decision": "PASS_CUMULATIVE_DRIFT_EVIDENCE_CONSTRUCTION_ONLY" if not errors else "FAIL_AUDIT_OR_GATE",
        "errors": errors,
        "runs": len(raw.get("runs", [])),
        "scheduled_rows": sum(len(r.get("rows", [])) for r in raw.get("runs", []) if isinstance(r, dict)),
        "physical_input_emissions": raw.get("physical_input_emissions"),
        "corruption_controls_rejected": controls,
        "raw_sha256": sha(raw_bytes),
        "cases_sha256": sha(case_bytes),
    }
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if any(out.iterdir()):
        raise SystemExit("STOP_AUDIT_OUTPUT_NOT_EMPTY")
    result_bytes = (json.dumps(result, sort_keys=True, indent=2) + "\n").encode()
    (out / "audit.json").write_bytes(result_bytes)
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

