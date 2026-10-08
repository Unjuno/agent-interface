"""Independent source-provenance and result-scope audit."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
expected = freeze["source_files"]
repo_root = ROOT.parent.parent.parent if ROOT.parent.name == "doom" else None
repo_paths = {
    "map01_overlap_controller_v39.py": "research/doom/map01_overlap_controller_v39.py",
    "persistent_planner_adapter_v2.py": "research/live_control/persistent_planner_adapter_v2.py",
    "doom_source_refresh_v1.py": "research/doom/doom_source_refresh_v1.py",
    "doom_typed_coast_backend_v1.py": "research/doom/doom_typed_coast_backend_v1.py",
    "executor_v5.py": "research/live_control/executor_v5.py",
    "executor_v12.py": "research/live_control/executor_v12.py",
    "test_cancel_invalidated_cover_order.main.py": "research/doom/test_cancel_invalidated_cover_order.py",
}


def source_path(name):
    local = ROOT / name
    if local.exists():
        return local
    if repo_root is not None:
        return repo_root / repo_paths[name]
    raise FileNotFoundError(name)


def git_blob_sha(path):
    data = source_path(path).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


for name, sha in expected.items():
    assert git_blob_sha(name) == sha, f"Git blob mismatch: {name}"

backend = source_path("doom_typed_coast_backend_v1.py").read_text(encoding="utf-8")
v5 = source_path("executor_v5.py").read_text(encoding="utf-8")
v12 = source_path("executor_v12.py").read_text(encoding="utf-8")
adapter = source_path("persistent_planner_adapter_v2.py").read_text(encoding="utf-8")
controller = source_path("map01_overlap_controller_v39.py").read_text(encoding="utf-8")
assert backend.index("self.emit(typed)") < backend.index("self.images.publish(frame)")
assert backend.index("self.images.publish(frame)") < backend.index('self.emit({"event": "observation"')
assert "from executor_v5 import Executor as Previous" in v12
assert v5.index("self.backend.execute(step,cancel,identifier,index)") < v5.index("event='terminal'")
assert adapter.index("self._cancellation_requested = True") < adapter.index("before_transport()")
assert adapter.index("before_transport()") < adapter.index("self.client.interrupt_turn(")
cancel = controller[controller.index("def cancel_invalidated_cover("):]
assert cancel.index("before_transport=cancel_executor_program") < cancel.index("terminal = wait(")

result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
assert result["classification"] == "CONSTRUCTION_ONLY_CURRENT_MAIN_FUNCTION_COMPOSITION"
assert result["source_commit"] == freeze["github_main_sha_at_freeze"]
assert result["timeline"] == ["executor_cancel_write", "executor_flush",
                               "planner_interrupt_request", "planner_interrupt_ack"]
assert result["verified_executor_release"] == {
    "verified": True, "keys_down": [], "buttons_down": []}
assert result["invalidated_planner_result"] == {
    "status": "completed", "answer_eligible": False,
    "cancellation_requested": True, "answer": None}
assert result["fresh_observation_used"]["sequence"] == 11
assert result["source_refresh_status"] == "already_observed"
assert result["next_turn_input"]["image_name"] == "next-temporal-sheet.png"
assert result["next_turn_input"]["prompt_has_fresh_health"] is True
assert result["next_turn_input"]["prompt_has_fresh_ammo"] is True
assert result["next_turn_input"]["latest_frame_pixel"] == [20, 180, 20]

for mode in ("normal", "optimized"):
    assert (ROOT / f"{mode}.exit").read_text(encoding="utf-8").strip() == "0"
    stderr = (ROOT / f"{mode}.stderr.txt").read_text(encoding="utf-8")
    assert "Ran 1 test" in stderr and "OK" in stderr

checks = {}
for path in sorted(ROOT.rglob("*")):
    if (path.is_file() and "__pycache__" not in path.parts and
            path.name not in set(expected) | {"SHA256SUMS.txt"}):
        checks[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
lines = [line.split("  ", 1) for line in (ROOT / "SHA256SUMS.txt").read_text().splitlines()]
assert {name: digest for digest, name in lines} == checks

print(json.dumps({"audit_passed": True, "main_sha": freeze["github_main_sha_at_freeze"],
                  "source_git_blobs": len(expected), "checked_package_files": len(checks),
                  "normal_and_optimized": "1/1 PASS each", "scoped_claim": result["classification"],
                  "producer_full_observation_before_terminal": True}, indent=2))
