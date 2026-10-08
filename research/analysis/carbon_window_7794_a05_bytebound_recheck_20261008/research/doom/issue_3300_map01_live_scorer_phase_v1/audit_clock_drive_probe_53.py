"""Independent stdlib audit for the excluded MAP01 drive-boundary probe."""
import hashlib
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "map01-clock-drive-probe"
raw_path = ROOT / "raw.json"
raw = json.loads(raw_path.read_text(encoding="utf-8"))
errors = []
expected_order = [
    "get_episode_time", "is_episode_finished", "is_player_dead",
    "get_game_variable", "get_game_variable", "get_ticrate",
    "is_episode_timeout_reached", "get_episode_time",
]
summary = {
    "schema": "map01-explicit-clock-drive-audit-v1",
    "formal_allocation": False,
    "errors": errors,
    "conditions": [],
}
if raw.get("formal_allocation") is not False:
    errors.append("raw_marked_formal")
if len(raw.get("conditions", [])) != 2:
    errors.append("expected_two_conditions")

for condition in raw.get("conditions", []):
    samples = condition.get("samples", [])
    name = condition.get("condition")
    tic_deltas = []
    scorer_spans = []
    drive_spans = []
    for index, sample in enumerate(samples):
        if sample.get("index") != index:
            errors.append(f"{name}:index:{index}")
        trace = sample.get("scorer_getter_trace", [])
        if [event.get("name") for event in trace] != expected_order:
            errors.append(f"{name}:getter_order:{index}")
            continue
        before, after = trace[0].get("result"), trace[-1].get("result")
        if before != after:
            errors.append(f"{name}:scorer_tic_bracket:{index}")
        if sample.get("scorer_return", {}).get("map_exit") != bool(
            trace[1].get("result") and not trace[2].get("result") and not trace[6].get("result")
        ):
            errors.append(f"{name}:score_reconstruction:{index}")
        returned = sample.get("scorer_return", {})
        reconstructed = {
            "kill_count": int(trace[3].get("result", -1)),
            "death_count": int(trace[4].get("result", -1)),
            "episode_finished": bool(trace[1].get("result")),
            "player_dead": bool(trace[2].get("result")),
            "map_exit": bool(trace[1].get("result") and not trace[2].get("result") and not trace[6].get("result")),
        }
        if any(returned.get(key) != value for key, value in reconstructed.items()):
            errors.append(f"{name}:returned_fields_not_reconstructed:{index}")
        if not (sample.get("scorer_start_ns", 0) <= returned.get("sample_ns", -1) <= sample.get("scorer_end_ns", 0)):
            errors.append(f"{name}:sample_timestamp_outside_outer_call:{index}")
        if sample.get("scorer_start_ns", 0) > trace[0].get("start_ns", 0):
            errors.append(f"{name}:scorer_start_order:{index}")
        if sample.get("scorer_end_ns", 0) < trace[-1].get("end_ns", 0):
            errors.append(f"{name}:scorer_end_order:{index}")
        tic_deltas.append(sample.get("tic_after_drive", 0) - sample.get("tic_before_drive", 0))
        scorer_spans.append(sample.get("scorer_end_ns", 0) - sample.get("scorer_start_ns", 0))
        drive_spans.append(sample.get("drive_end_ns", 0) - sample.get("drive_start_ns", 0))

    if len(samples) != 20 or condition.get("closed") is not True or condition.get("error"):
        errors.append(f"{name}:row_count_or_cleanup")
    if condition.get("end_tic", 0) < condition.get("start_tic", 0):
        errors.append(f"{name}:tic_regressed")
    elapsed_ns = samples[-1].get("observed_elapsed_ns", 0) if samples else 0
    summary["conditions"].append({
        "name": name,
        "rows": len(samples),
        "start_tic": condition.get("start_tic"),
        "end_tic": condition.get("end_tic"),
        "net_tic_delta": condition.get("end_tic", 0) - condition.get("start_tic", 0),
        "per_call_tic_delta_counts": {str(v): tic_deltas.count(v) for v in sorted(set(tic_deltas))},
        "elapsed_ms_to_last_sample": round(elapsed_ns / 1e6, 3),
        "observed_tic_hz_net_over_elapsed": round(
            (condition.get("end_tic", 0) - condition.get("start_tic", 0)) * 1e9 / elapsed_ns, 3
        ) if elapsed_ns else None,
        "drive_span_ms_min_max": [round(min(drive_spans) / 1e6, 3), round(max(drive_spans) / 1e6, 3)] if drive_spans else None,
        "scorer_span_us_min_max": [round(min(scorer_spans) / 1e3, 2), round(max(scorer_spans) / 1e3, 2)] if scorer_spans else None,
        "scorer_span_us_median": round(statistics.median(scorer_spans) / 1e3, 2) if scorer_spans else None,
        "all_same_tic_scorer_brackets": len(samples) == 20 and not any(
            [e.get("result") for e in x.get("scorer_getter_trace", []) if e.get("name") == "get_episode_time"][0]
            != [e.get("result") for e in x.get("scorer_getter_trace", []) if e.get("name") == "get_episode_time"][1]
            for x in samples
        ),
    })

conditions = {x["name"]: x for x in summary["conditions"]}
if conditions.get("passive", {}).get("net_tic_delta") != 0:
    errors.append("passive_control_tic_changed")
if conditions.get("paced_advance_action_1", {}).get("net_tic_delta", 0) <= 0:
    errors.append("paced_action_did_not_advance_public_snapshot")
summary["audit_disposition"] = "PASS_CONSTRUCTION_ONLY_EXPLICIT_ACTION_BOUNDARY" if not errors else "FAIL_AUDIT"
summary["raw_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
summary["runner_sha256"] = hashlib.sha256(Path(__file__).resolve().parent.joinpath("map01_clock_drive_probe.py").read_bytes()).hexdigest()
audit_path = ROOT / "audit.json"
audit_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(summary, indent=2, sort_keys=True))
raise SystemExit(bool(errors))
