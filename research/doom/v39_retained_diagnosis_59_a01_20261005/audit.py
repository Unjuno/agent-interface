"""Independent raw-only checks for the read-only V39 diagnosis result."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text())
result = json.loads((HERE / "RESULT.json").read_text())
raw_by_path = {}
for path, pin in freeze["inputs"].items():
    raw = subprocess.check_output(
        ["git", "show", f"{freeze['source_commit']}:{path}"], cwd=ROOT
    )
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{freeze['source_commit']}:{path}"],
        cwd=ROOT, text=True,
    ).strip()
    assert blob == pin["git_blob"]
    assert hashlib.sha256(raw).hexdigest() == pin["sha256"]
    assert len(raw) == pin["bytes"]
    raw_by_path[path] = raw
report = json.loads(raw_by_path[
    "research/doom/results/map01-v39-coast-liveness-live-01/report.json"
])
events = [json.loads(line) for line in raw_by_path[
    "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl"
].splitlines()]
assert result["classification"] == "PASS_DESCRIPTIVE_DIAGNOSIS_ONLY"
assert len(result["decisions"]) == 6
assert result["event_rows"] == 634
assert result["typed_observations"] == 218
assert len(events) == result["event_rows"]
assert sum(row.get("event") == "typed_observation" for row in events) == result["typed_observations"]
assert result["aggregate_score"]["rows"] == 1
score_rows = [row for row in events if row.get("event") == "post_control_score"]
assert len(score_rows) == result["aggregate_score"]["rows"]
assert score_rows[0] == report["score"]
assert result["aggregate_score"]["map_exit"] is False
assert result["aggregate_score"]["player_dead"] is False
assert result["aggregate_score"]["kills"] == 1
assert [d["cover_policy_actions"] for d in result["decisions"]] == [
    [],
    [{"action": "strafe_right", "extent": "short"},
     {"action": "strafe_left", "extent": "short"},
     {"action": "retreat_fire", "extent": "short"}],
    [], [],
    [{"action": "strafe_right", "extent": "short"},
     {"action": "strafe_left", "extent": "short"},
     {"action": "retreat_fire", "extent": "short"}],
    [{"action": "strafe_right", "extent": "short"},
     {"action": "strafe_left", "extent": "short"},
     {"action": "retreat_fire", "extent": "short"}],
]
assert [d["cover_policy_source_iteration"] for d in result["decisions"]] == [
    None, 0, None, None, 3, 4,
]
typed_by_id = {}
for row in events:
    if row.get("event") == "typed_observation":
        typed_by_id.setdefault(row["id"], []).append(row)
for raw_decision, summarized in zip(report["decisions"], result["decisions"]):
    assert raw_decision["iteration"] == summarized["iteration"]
    assert raw_decision.get("cover_policy") == summarized["cover_policy_actions"]
    assert raw_decision.get("cover_policy_source_iteration") == summarized["cover_policy_source_iteration"]
    assert raw_decision.get("model_ns") / 1_000_000 == summarized["model_wait_ms"] or abs(
        raw_decision.get("model_ns") / 1_000_000 - summarized["model_wait_ms"]
    ) < 0.001
    typed = typed_by_id.get(summarized["cover_id"], [])
    assert len(typed) == summarized["typed_observation_count"]
    for signal in ("health", "ammo"):
        values = [row["signals"][signal]["value"] for row in typed
                  if row.get("signals", {}).get(signal, {}).get("status") == "observed"]
        expected = summarized[f"{signal}_first_last"]
        assert ([values[0], values[-1]] if values else None) == expected
    assert (raw_decision.get("final_action_admission") or {}).get("status") == summarized[
        "returned_action_admission"
    ]
assert [d["returned_action_admission"] for d in result["decisions"]] == [
    "INPUT_ADMITTED", "REJECTED_ACTION_NOT_CURRENT", "REJECTED_ACTION_NOT_CURRENT",
    "INPUT_ADMITTED", "INPUT_ADMITTED", "REJECTED_POLICY_INVALIDATED",
]
assert result["decisions"][5]["policy_invalidation"]["outcome"]["reason"] == "below_hard_minimum"
assert result["decisions"][5]["policy_invalidation"]["outcome"]["task_success_verified"] is False
assert result["decisions"][0]["cover_policy_actions"] == []
assert result["decisions"][0]["next_cover_authored"]
assert result["decisions"][1]["cover_policy_source_iteration"] == 0
assert all(r["scope"] == "viewport pixels only"
           for d in result["decisions"] for r in d["effect_receipts"])
assert result["limitations"]["threat_descriptions_are_model_authored"] is True
assert result["limitations"]["independent_per_decision_task_effect"] is False
assert result["limitations"]["matched_fixed_safe_counterfactual"] is False
assert result["limitations"]["live_run_or_replay_performed"] is False
print("AUDIT_PASS: source-bound six-turn diagnosis; aggregate-only score and effect limits preserved")
