import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text())
RESULT = json.loads((HERE / "RESULT.json").read_text())


def blob(path):
    rel = path.relative_to(REPO).as_posix()
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"HEAD:{rel}"], text=True).strip()


expected = {
    "research/doom/map01_overlap_controller_v39.py": "f7b66279d87ebc3704ccef1b6a5ce646611c890b",
    "research/doom/doom_source_refresh_v1.py": "6b5add0fa29865de64afcfa1da4a272d9a216e8d",
    "research/live_control/persistent_planner_adapter_v2.py": "879736562aa5c0637319616c9f01df22af087b15",
    "research/doom/doom_typed_coast_backend_v1.py": "d95d382ee9c234dab652fa8af93b233baa5225a4",
    "research/doom/doom_typed_observation_v1.py": "930e1c78511b57999a0a2176cb94a31a32d166a8",
}
assert FREEZE["main_sha"] == "2a9052efdd155b8cdc173d216a969ea5f64a1ce9"
assert FREEZE["sources"] == expected
actual = {name: blob(REPO / name) for name in expected}
assert actual == expected
assert RESULT["source_blobs"] == {"controller": expected["research/doom/map01_overlap_controller_v39.py"],
                                  "source_refresh": expected["research/doom/doom_source_refresh_v1.py"],
                                  "adapter": expected["research/live_control/persistent_planner_adapter_v2.py"],
                                  "typed_backend": expected["research/doom/doom_typed_coast_backend_v1.py"],
                                  "typed_observation": expected["research/doom/doom_typed_observation_v1.py"]}
assert RESULT["disposition"] == "PASS_CANDIDATE_COMPOSITION"
assert RESULT["format"] == "v39-preacceptance-stale-replan-a02"
assert RESULT["trigger"] == {"submitted_sequence": 1, "producer_sequence_at_rejection": 2,
                             "rejection_before_typed_observation": True,
                             "typed_observation_before_full_artifact": True,
                             "exact_producer_snapshot_executed": True,
                             "typed_and_full_sequence": 2,
                             "typed_and_full_frame_hash_match": True}
assert RESULT["first_turn"] == {"answer": "stale-turn-answer", "used_after_rejection": False}
recovery = RESULT["recovery"]
assert recovery["fresh_sequence"] == 2 and recovery["fresh_capture_ns"] > 100
assert recovery["fresh_hud_in_prompt"] == {"health": 86, "ammo": 12}
assert recovery["fresh_image_used"] == "fixture/sequence-2.png"
assert recovery["planner_turn_count"] == 2 and recovery["controller_wait_advanced_latest"] is True
assert recovery["typed_capture_matches_full_frame"] is True
assert recovery["action_resubmissions_after_rejection"] == 0
assert RESULT["existing_source_refresh"] == {"status": "already_observed", "submit_count": 0,
                                              "returned_sequence": 1}
assert RESULT["controls"] == {"non_stale_rejection": "refused", "binding_change": "refused",
                              "no_fresh_observation": "refused", "typed_full_hash_mismatch": "refused",
                              "missing_typed_event": "refused"}

# Independent source-shape checks for the exact functions under test.
tree = ast.parse((REPO / "research/doom/map01_overlap_controller_v39.py").read_text())
wait = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "wait"]
begin = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "begin_model_turn"]
assert len(wait) == 1 and len(begin) == 1
wait_source = ast.get_source_segment((REPO / "research/doom/map01_overlap_controller_v39.py").read_text(), wait[0])
assert 'if row["event"] == "observation":' in wait_source and "latest = row" in wait_source
begin_source = ast.get_source_segment((REPO / "research/doom/map01_overlap_controller_v39.py").read_text(), begin[0])
assert "source_health" in begin_source and "source_ammo" in begin_source and "image_path=win(image)" in begin_source
backend_source = (REPO / "research/doom/doom_typed_coast_backend_v1.py").read_text()
backend_tree = ast.parse(backend_source)
snapshot = next(node for node in ast.walk(backend_tree)
                if isinstance(node, ast.FunctionDef) and node.name == "snapshot")
emit_calls = sorted((node for node in ast.walk(snapshot)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                     and node.func.attr == "emit"), key=lambda node: node.lineno)
assert len(emit_calls) >= 2
assert isinstance(emit_calls[0].args[0], ast.Name) and emit_calls[0].args[0].id == "typed"
full_event = emit_calls[1].args[0]
assert isinstance(full_event, ast.Dict)
event_fields = {key.value: value.value for key, value in zip(full_event.keys, full_event.values)
                if isinstance(key, ast.Constant) and isinstance(value, ast.Constant)}
assert event_fields.get("event") == "observation"
assert emit_calls[0].lineno < emit_calls[1].lineno
sequence_increments = [node for node in ast.walk(snapshot) if isinstance(node, ast.AugAssign)
                       and isinstance(node.target, ast.Attribute) and node.target.attr == "sequence"]
assert len(sequence_increments) == 1 and sequence_increments[0].lineno < emit_calls[0].lineno
typed_source = (REPO / "research/doom/doom_typed_observation_v1.py").read_text()
assert 'SCHEMA = "doom-typed-observation-v1"' in typed_source
assert '"event": "typed_observation"' in typed_source
for line in (HERE / "SHA256SUMS.txt").read_text().splitlines():
    digest, name = line.split("  ", 1)
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
print("PASS: pinned producer order, paired sequence-2 turn, zero resubmit, and five fail-closed controls")
