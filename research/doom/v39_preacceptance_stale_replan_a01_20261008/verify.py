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
}
assert FREEZE["main_sha"] == "3d5f91f4409a79eabb332187d7ad2639ec8106c9"
assert FREEZE["sources"] == expected
actual = {name: blob(REPO / name) for name in expected}
assert actual == expected
assert RESULT["source_blobs"] == {"controller": expected["research/doom/map01_overlap_controller_v39.py"],
                                  "source_refresh": expected["research/doom/doom_source_refresh_v1.py"],
                                  "adapter": expected["research/live_control/persistent_planner_adapter_v2.py"]}
assert RESULT["disposition"] == "PASS_CANDIDATE_COMPOSITION"
assert RESULT["trigger"] == {"submitted_sequence": 1, "producer_sequence_at_rejection": 2,
                             "rejection_before_full_observation_delivery": True}
assert RESULT["first_turn"] == {"answer": "stale-turn-answer", "used_after_rejection": False}
recovery = RESULT["recovery"]
assert recovery["fresh_sequence"] == 2 and recovery["fresh_capture_ns"] > 100
assert recovery["fresh_hud_in_prompt"] == {"health": 86, "ammo": 12}
assert recovery["fresh_image_used"] == "fixture/sequence-2.png"
assert recovery["planner_turn_count"] == 2 and recovery["controller_wait_advanced_latest"] is True
assert recovery["action_resubmissions_after_rejection"] == 0
assert RESULT["existing_source_refresh"] == {"status": "already_observed", "submit_count": 0,
                                              "returned_sequence": 1}
assert RESULT["controls"] == {"non_stale_rejection": "refused", "binding_change": "refused",
                              "no_fresh_observation": "refused"}

# Independent source-shape checks for the exact functions under test.
tree = ast.parse((REPO / "research/doom/map01_overlap_controller_v39.py").read_text())
wait = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "wait"]
begin = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "begin_model_turn"]
assert len(wait) == 1 and len(begin) == 1
wait_source = ast.get_source_segment((REPO / "research/doom/map01_overlap_controller_v39.py").read_text(), wait[0])
assert 'if row["event"] == "observation":' in wait_source and "latest = row" in wait_source
begin_source = ast.get_source_segment((REPO / "research/doom/map01_overlap_controller_v39.py").read_text(), begin[0])
assert "source_health" in begin_source and "source_ammo" in begin_source and "image_path=win(image)" in begin_source
for line in (HERE / "SHA256SUMS.txt").read_text().splitlines():
    digest, name = line.split("  ", 1)
    assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
print("PASS: pinned source, sequence-2 turn, zero resubmit, and three fail-closed controls")
