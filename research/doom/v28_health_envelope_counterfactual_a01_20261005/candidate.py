"""Replay exact retained V28 source/trigger signal pairs through the pinned V39 guard."""
import ast
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULT = REPO / "research/doom/results/map01-fixed-threat-v28-live-01"
CONTROLLER = REPO / "research/doom/map01_overlap_controller_v39.py"
GUARD_SOURCE = REPO / "research/live_control/observable_signal_guard_v2.py"
if len(sys.argv) != 2:
    raise SystemExit("usage: candidate.py NEW_RAW_OUTPUT.json")
OUT = Path(sys.argv[1]).resolve()
if OUT.exists():
    raise SystemExit(f"refusing to overwrite existing output: {OUT}")
OUT.parent.mkdir(parents=True, exist_ok=True)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_from_source(path, name, scope):
    tree = ast.parse(path.read_bytes())
    node = next(item for item in tree.body
                if isinstance(item, ast.FunctionDef) and item.name == name)
    module = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(module, str(path), "exec"), scope)
    return scope[name]


review_path = RESULT / "analysis/threat-review.json"
events_path = RESULT / "runtime/events.jsonl"
report_path = RESULT / "report.json"
audit_path = RESULT / "audit.json"
review = read_json(review_path)
report = read_json(report_path)
existing_audit = read_json(audit_path)
events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
if (review.get("allocation_id") != "map01-fixed-threat-v28-live-01" or
        existing_audit.get("passed") is not True or
        existing_audit.get("disposition") != "RETAINED_NATURAL_INVALIDATION_PASS_WITH_REPLAN_STARVATION"):
    raise SystemExit("retained V28 source audit identity/disposition mismatch")
frames = {Path(row["frame"]).name: row for row in review["rows"]}
observations = {Path(row.get("image", "")).name: row for row in events
                if row.get("event") == "observation" and row.get("image")}
binding = {"focus": 1, "surface": 1, "geometry": [0, 0, 1, 1]}
scope = {}
guard_spec = function_from_source(CONTROLLER, "guard_spec", scope)
ammo_guard_spec = function_from_source(CONTROLLER, "ammo_guard_spec", scope)
sys.path.insert(0, str(GUARD_SOURCE.parent))
from observable_signal_guard_v2 import ObservableSignalGuard

selected = []
for decision in report["decisions"]:
    if decision["iteration"] not in (0, 2, 3, 4, 5):
        continue
    invalidation = decision.get("policy_invalidation")
    if (decision.get("planner_turn_status") != "interrupted" or
            type(invalidation) is not dict):
        raise SystemExit("selected V28 span is not an invalidated planner decision")
    source_name = Path(decision["source_image"]).name
    target_name = Path(invalidation["image"]).name
    source_review, target_review = frames[source_name], frames[target_name]
    source_event, target_event = observations[source_name], observations[target_name]
    if (not source_review["exact"] or not target_review["exact"] or
            not source_review["visible_enemy"] or not target_review["visible_enemy"] or
            target_event["sequence"] != invalidation["sequence"] or
            target_event["image"] != invalidation["image"] or
            target_event["sequence"] <= source_event["sequence"] or
            target_event["capture_ns"] <= source_event["capture_ns"]):
        raise SystemExit(f"exact source/trigger join failed for decision {decision['iteration']}")
    selected.append({
        "iteration": decision["iteration"],
        "source_frame": source_name,
        "source_frame_sha256": source_review["sha256"],
        "source_sequence": source_event["sequence"],
        "source_capture_ns": source_event["capture_ns"],
        "source_health": source_review["health"],
        "source_ammo": source_review["ammo"],
        "trigger_frame": target_name,
        "trigger_frame_sha256": target_review["sha256"],
        "trigger_sequence": target_event["sequence"],
        "trigger_capture_ns": target_event["capture_ns"],
        "trigger_health": target_review["health"],
        "trigger_ammo": target_review["ammo"],
        "prior_cover_source_iteration": decision.get("cover_policy_source_iteration"),
        "prior_cover": decision.get("cover_policy"),
    })
if [row["iteration"] for row in selected] != [0, 2, 3, 4, 5]:
    raise SystemExit("selected V28 invalidation decision set changed")

sweep = []
for loss in range(21):
    rows = []
    for span in selected:
        source_health = {
            "status": "observed", "signal_id": "health", "sequence": span["source_sequence"],
            "value": span["source_health"], "capture_ns": span["source_capture_ns"],
            "binding": binding,
        }
        source_ammo = {
            "status": "observed", "signal_id": "ammo", "sequence": span["source_sequence"],
            "value": span["source_ammo"], "capture_ns": span["source_capture_ns"],
            "binding": binding,
        }
        health_validity = {
            "signal_id": "health", "critical_health_minimum": 35,
            "maximum_health_loss": loss, "max_source_age_ms": 30000,
        }
        health_spec = guard_spec(health_validity, source_health, span["iteration"])
        ammo_spec = ammo_guard_spec(source_ammo, span["iteration"], 30000)
        health_guard = ObservableSignalGuard(health_spec, source_health, binding)
        ammo_guard = ObservableSignalGuard(ammo_spec, source_ammo, binding)
        target_health = {
            "status": "observed", "signal_id": "health", "sequence": span["trigger_sequence"],
            "value": span["trigger_health"], "capture_ns": span["trigger_capture_ns"],
            "binding": binding,
        }
        target_ammo = {
            "status": "observed", "signal_id": "ammo", "sequence": span["trigger_sequence"],
            "value": span["trigger_ammo"], "capture_ns": span["trigger_capture_ns"],
            "binding": binding,
        }
        health_outcome = health_guard.evaluate(target_health)
        ammo_outcome = ammo_guard.evaluate(target_ammo)
        rows.append({
            "iteration": span["iteration"],
            "source_health": span["source_health"],
            "trigger_health": span["trigger_health"],
            "health_loss": span["source_health"] - span["trigger_health"],
            "effective_hard_floor": health_spec["hard_minimum"],
            "health_status": health_outcome["status"],
            "health_reason": health_outcome["reason"],
            "ammo_source": span["source_ammo"],
            "ammo_trigger": span["trigger_ammo"],
            "ammo_status": ammo_outcome["status"],
            "ammo_reason": ammo_outcome["reason"],
            "source_age_ms": health_outcome["source_age_ms"],
        })
    sweep.append({
        "maximum_health_loss": loss,
        "planner_interruption_count": sum(row["health_status"] == "HARD_INVALIDATED" or
                                            row["ammo_status"] == "HARD_INVALIDATED"
                                            for row in rows),
        "soft_health_changes": sum(row["health_status"] == "SOFT_CHANGED" for row in rows),
        "soft_ammo_changes": sum(row["ammo_status"] == "SOFT_CHANGED" for row in rows),
        "span_outcomes": rows,
    })

raw = {
    "schema": "v28-health-envelope-counterfactual-raw-v1",
    "source_main": "6a2826d391b77496b69752609a6f07b6971b4b6f",
    "source_sha256": {
        "report": sha256(report_path), "existing_audit": sha256(audit_path),
        "review": sha256(review_path), "events": sha256(events_path),
        "controller": sha256(CONTROLLER), "guard": sha256(GUARD_SOURCE),
    },
    "allocation_id": review["allocation_id"],
    "method": "exact source/trigger pairs from five interrupted report rows evaluated by pinned V39 health/ammo guard; all permitted loss values enumerated",
    "guard_binding": binding,
    "critical_health_minimum": 35,
    "max_source_age_ms": 30000,
    "assumed_re_admission": "each source/trigger pair uses its own exact observed source row; no within-span reset",
    "spans": selected,
    "sweep": sweep,
    "live_game": False,
    "model_calls": 0,
    "gui": False,
    "x_server": False,
    "os_input": False,
    "allocation": False,
}
OUT.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({
    "output": str(OUT),
    "spans": len(selected),
    "threshold_counts": {str(row["maximum_health_loss"]): row["planner_interruption_count"]
                         for row in sweep},
    "candidate_sha256": sha256(Path(__file__)),
}, indent=2))
