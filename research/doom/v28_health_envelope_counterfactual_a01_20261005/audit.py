"""Independent audit of the A01 raw replay; does not import candidate code."""
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULT = REPO / "research/doom/results/map01-fixed-threat-v28-live-01"
CONTROLLER = REPO / "research/doom/map01_overlap_controller_v39.py"
GUARD = REPO / "research/live_control/observable_signal_guard_v2.py"
if len(sys.argv) != 3:
    raise SystemExit("usage: audit.py RAW.json NEW_AUDIT.json")
raw_path, audit_path = (Path(value).resolve() for value in sys.argv[1:])
if audit_path.exists():
    raise SystemExit(f"refusing to overwrite existing audit: {audit_path}")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


raw = load(raw_path)
paths = {
    "report": RESULT / "report.json",
    "existing_audit": RESULT / "audit.json",
    "review": RESULT / "analysis/threat-review.json",
    "events": RESULT / "runtime/events.jsonl",
    "controller": CONTROLLER,
    "guard": GUARD,
}
if raw.get("schema") != "v28-health-envelope-counterfactual-raw-v1":
    raise SystemExit("raw schema mismatch")
if raw.get("source_main") != "6a2826d391b77496b69752609a6f07b6971b4b6f":
    raise SystemExit("pinned main mismatch")
actual_hashes = {key: digest(path) for key, path in paths.items()}
if raw.get("source_sha256") != actual_hashes:
    raise SystemExit("raw source hash set does not match retained evidence")

review, report = load(paths["review"]), load(paths["report"])
events = [json.loads(line) for line in paths["events"].read_text(encoding="utf-8").splitlines()]
frames = {Path(item["frame"]).name: item for item in review["rows"]}
observations = {Path(item["image"]).name: item for item in events
                if item.get("event") == "observation" and item.get("image")}
decisions = {item["iteration"]: item for item in report["decisions"]}
expected_iterations = [0, 2, 3, 4, 5]
if [item.get("iteration") for item in raw.get("spans", [])] != expected_iterations:
    raise SystemExit("span set mismatch")
expected_spans = []
for iteration in expected_iterations:
    decision = decisions[iteration]
    invalidation = decision.get("policy_invalidation")
    if decision.get("planner_turn_status") != "interrupted" or type(invalidation) is not dict:
        raise SystemExit(f"V28 decision {iteration} is not an interrupted invalidation")
    source_name, trigger_name = Path(decision["source_image"]).name, Path(invalidation["image"]).name
    source, trigger = frames[source_name], frames[trigger_name]
    source_event, trigger_event = observations[source_name], observations[trigger_name]
    if (not source.get("exact") or not trigger.get("exact") or
            not source.get("visible_enemy") or not trigger.get("visible_enemy") or
            invalidation.get("sequence") != trigger_event.get("sequence") or
            invalidation.get("image") != trigger_event.get("image")):
        raise SystemExit(f"frame/event cross-check failed for {iteration}")
    expected_spans.append({
        "iteration": iteration, "source_frame": source_name,
        "source_frame_sha256": source["sha256"],
        "source_sequence": source_event["sequence"],
        "source_capture_ns": source_event["capture_ns"],
        "source_health": source["health"], "source_ammo": source["ammo"],
        "trigger_frame": trigger_name, "trigger_frame_sha256": trigger["sha256"],
        "trigger_sequence": trigger_event["sequence"],
        "trigger_capture_ns": trigger_event["capture_ns"],
        "trigger_health": trigger["health"], "trigger_ammo": trigger["ammo"],
        "prior_cover_source_iteration": decision.get("cover_policy_source_iteration"),
        "prior_cover": decision.get("cover_policy"),
    })
if raw.get("spans") != expected_spans:
    raise SystemExit("raw span transcription mismatch")

if (raw.get("critical_health_minimum") != 35 or raw.get("max_source_age_ms") != 30000 or
        raw.get("guard_binding") != {"focus": 1, "surface": 1, "geometry": [0, 0, 1, 1]}):
    raise SystemExit("frozen guard parameters mismatch")
if raw.get("live_game") is not False or raw.get("model_calls") != 0 or raw.get("gui") is not False or raw.get("x_server") is not False or raw.get("os_input") is not False or raw.get("allocation") is not False:
    raise SystemExit("out-of-scope activity marker mismatch")

expected_sweep = []
for loss in range(21):
    span_rows = []
    for span in expected_spans:
        elapsed = span["trigger_capture_ns"] - span["source_capture_ns"]
        age_ms = elapsed / 1_000_000
        health_floor = max(35, span["source_health"] - loss)
        health_loss = span["source_health"] - span["trigger_health"]
        if elapsed <= 0 or age_ms > 30000:
            health_status, health_reason = "UNKNOWN", "source_expired" if age_ms > 30000 else "invalid_sample_time"
        elif span["trigger_health"] < health_floor:
            health_status, health_reason = "HARD_INVALIDATED", "below_hard_minimum"
        elif span["trigger_health"] != span["source_health"]:
            health_status, health_reason = "SOFT_CHANGED", "within_validity_envelope"
        else:
            health_status, health_reason = "UNCHANGED", "signal_unchanged"
        if span["trigger_ammo"] < 1:
            ammo_status, ammo_reason = "HARD_INVALIDATED", "below_hard_minimum"
        elif span["trigger_ammo"] != span["source_ammo"]:
            ammo_status, ammo_reason = "SOFT_CHANGED", "within_validity_envelope"
        else:
            ammo_status, ammo_reason = "UNCHANGED", "signal_unchanged"
        span_rows.append({
            "iteration": span["iteration"], "source_health": span["source_health"],
            "trigger_health": span["trigger_health"], "health_loss": health_loss,
            "effective_hard_floor": health_floor, "health_status": health_status,
            "health_reason": health_reason, "ammo_source": span["source_ammo"],
            "ammo_trigger": span["trigger_ammo"], "ammo_status": ammo_status,
            "ammo_reason": ammo_reason, "source_age_ms": age_ms,
        })
    expected_sweep.append({
        "maximum_health_loss": loss,
        "planner_interruption_count": sum(row["health_status"] == "HARD_INVALIDATED" or row["ammo_status"] == "HARD_INVALIDATED" for row in span_rows),
        "soft_health_changes": sum(row["health_status"] == "SOFT_CHANGED" for row in span_rows),
        "soft_ammo_changes": sum(row["ammo_status"] == "SOFT_CHANGED" for row in span_rows),
        "span_outcomes": span_rows,
    })
if raw.get("sweep") != expected_sweep:
    raise SystemExit("sweep outcome mismatch")

counts = [row["planner_interruption_count"] for row in expected_sweep]
if counts != [5, 5, 4, 3, 3, 3] + [0] * 15:
    raise SystemExit("unexpected interruption count curve")
audit = {
    "schema": "v28-health-envelope-counterfactual-audit-v1",
    "passed": True,
    "disposition": "PASS_COUNTERFACTUAL_REPLAY",
    "raw_sha256": digest(raw_path),
    "source_sha256": actual_hashes,
    "spans_independently_reconstructed": len(expected_spans),
    "loss_values_independently_recomputed": len(expected_sweep),
    "interruption_counts_by_loss_0_to_20": counts,
    "scope": "offline five-span historical counterfactual; no live game, model, GUI, OS input, or allocation",
    "limitations": [
        "historical invalidations were caused by a changed-pixel region guard, not typed health alone",
        "no causal damage attribution or within-span observation replay",
        "does not establish tactical appropriateness or Issue 59 completion",
    ],
}
audit_path.parent.mkdir(parents=True, exist_ok=True)
audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"audit": str(audit_path), "passed": True, "counts": counts}, indent=2))
