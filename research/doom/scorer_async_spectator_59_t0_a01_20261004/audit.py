"""Independent raw audit for SCORER-REFRESH-59-ASYNC-SPECTATOR-01."""
from pathlib import Path
import ast, hashlib, json, sys

root = Path(__file__).resolve().parent
freeze = json.loads((root / "FREEZE.json").read_text())
pins = json.loads((root / "SOURCE_PINS.json").read_text())
raw = json.loads((root / "raw.json").read_text())
host = json.loads((root / "host.json").read_text())
source = (root / "experiment.py").read_bytes()
comparator = (root / "candidate_guard.py").read_bytes()
errors = []

def require(ok, reason):
    if not ok:
        errors.append(reason)

require(hashlib.sha256(source).hexdigest() == freeze["source"]["sha256"], "candidate_source_hash")
require(hashlib.sha256(comparator).hexdigest() == pins["guard"]["sha256"], "comparator_source_hash")
require(hashlib.sha256((root / "target_session_map01_v12.py").read_bytes()).hexdigest() == freeze["target_session_source"]["sha256"], "target_session_source_hash")
sys.path.insert(0, str(root))
from candidate_guard import audit_refresh
comparator_result = audit_refresh({"status":"REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING", "tic_before":1, "tic_after":11, "tic_after_read":11})
require(comparator_result == {"qualified":False,"reason":"tic_did_not_advance_exactly_one"}, "candidate_guard_decision")
require(raw["allocation"] == freeze["id"], "allocation_identity")
require(raw["version"] == freeze["runtime"]["version"] == "1.3.0", "runtime_version")
require(raw["wad_sha256"] == freeze["runtime"]["expected_freedoom2_sha256"], "wad_hash")
require(raw["mode_actual"] == "Mode.ASYNC_SPECTATOR", "actual_mode")
require(raw["ticrate"] == 35, "ticrate")
require(raw["available_buttons"] == [], "available_buttons_not_empty")
require(raw["positive_input_calls"] == 0, "candidate_positive_input_counter")
require(raw["game_close_returned"] is True, "game_close")
require(host["status"] == "COMPLETED" and host["exit_code"] == 0, "host_process_exit")

calls = []
parsed = ast.parse(source)
for node in ast.walk(parsed):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "game":
        calls.append(node.func.attr)
require(calls.count("advance_action") == 1, "advance_action_count")
require(not ({"make_action", "set_action", "send_game_command", "add_game_command"} & set(calls)), "positive_input_api_found")

samples = {row["label"]: row for row in raw["samples"]}
pre = samples.get("before_acknowledged_update", {})
post = samples.get("after_acknowledged_update", {})
initial = samples.get("initial", {})
passive = samples.get("after_passive_150ms", {})
update = raw.get("update", {})
require(initial.get("state_tic") == passive.get("state_tic") == 1, "passive_state_tic_changed")
require(initial.get("episode_before") == passive.get("episode_after") == 1, "passive_episode_time_changed")
require(pre.get("state_tic") == update.get("episode_before") == 1, "pre_refresh_tic")
require(post.get("state_tic") == update.get("episode_after") == 11, "post_refresh_snapshot_tic")
require(update.get("delta") == 10, "refresh_delta")
require(post.get("state_variables") == [0.0, 0.0], "snapshot_score_values")
require(post.get("kill_live") == 0.0 and post.get("death_live") == 0.0, "live_score_values")
require(raw.get("status") == "PASS_COUNTEREXAMPLE_EXACT_ONE_TIC_GUARD", "candidate_disposition")

# Apply the preregistered exact-one-tic guard to the observed interval independently.
exact_one_guard = (type(update.get("episode_before")) is int and
                   type(update.get("episode_after")) is int and
                   update["episode_after"] == update["episode_before"] + 1)
require(not exact_one_guard, "counterexample_not_reproduced")
result = {
    "audit": "PASS_RAW_COUNTEREXAMPLE",
    "errors": errors,
    "allocation": freeze["id"],
    "candidate_source_sha256": hashlib.sha256(source).hexdigest(),
    "candidate_guard_source_sha256": hashlib.sha256(comparator).hexdigest(),
    "candidate_guard_result": comparator_result,
    "mode": raw["mode_actual"],
    "passive_episode_tic": [initial.get("episode_before"), passive.get("episode_after")],
    "acknowledged_update_episode_tic": [update.get("episode_before"), update.get("episode_after")],
    "acknowledged_update_delta": update.get("delta"),
    "post_update_state_tic": post.get("state_tic"),
    "score_values_unchanged_zero": True,
    "interpretation": "Exact-one-tic guard rejects this successful neutral ASYNC_SPECTATOR update; no claim of changed-score freshness or useful task effect.",
    "limits": raw["scope"],
}
(root / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
sys.exit(bool(errors))
