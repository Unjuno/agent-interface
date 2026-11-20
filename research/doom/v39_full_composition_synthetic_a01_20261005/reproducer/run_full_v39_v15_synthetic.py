"""One-shot V39 -> real V15 -> real V12/Executor/backend/owner fake-seam run."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import threading

ROOT = Path(os.environ.get("V39_SYNTHETIC_SOURCE_ROOT",
                           Path(__file__).resolve().parents[2])).resolve()
sys.path[:0] = [str(ROOT), str(ROOT / "research/doom"), str(ROOT / "research/live_control")]
import map01_overlap_controller_v39 as controller

WORK = Path(os.environ["V39_SYNTHETIC_WORK"]).resolve() if "V39_SYNTHETIC_WORK" in os.environ \
    else Path(tempfile.mkdtemp(prefix="v39-full-")).resolve()
WORK.mkdir(parents=True, exist_ok=False)
OUT = WORK / "run"
SHIM = str(Path(__file__).resolve().parent)

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

from PIL import Image
save = WORK / "fixture-save.png"
frame = WORK / "fixture-source.png"
Image.new("RGB", (640, 480), (1, 2, 3)).save(save)
Image.new("RGB", (640, 480), (3, 2, 1)).save(frame)
wad = Path(tempfile.gettempdir()) / "fake_vizdoom" / "freedoom2.wad"
wad.parent.mkdir(parents=True, exist_ok=True)
wad.write_bytes(b"synthetic-wad")
binding = {"focus": 41, "surface": 41, "geometry": [0, 0, 640, 480]}
fixture = {
    "schema": "map01_os_input_fixture_v1", "map": "MAP01", "skill": 1,
    "vizdoom": "synthetic-1", "iwad_sha256": digest(wad),
    "save_file": save.name, "save_sha256": digest(save),
    "source_frame": frame.name, "source_frame_sha256": digest(frame),
    "episode_tic": 0,
    "source_observation": {"event": "observation", "exact": True,
        "sequence": 1, "capture_ns": 1, "pointer_binding": binding},
    "setup_input_contract": ("fixture state reached through the same X11 Executor and "
        "recorded OS-input/coast programs; save is setup-only"),
}
fixture_path = WORK / "fixture.json"
fixture_path.write_text(json.dumps(fixture), encoding="utf-8")

action = {
    "assessment": "synthetic single action through the selected runtime path",
    "state": "active",
    "commands": [{"action": "fire", "extent": "pulse"}],
    "contingencies": [],
    "next_cover": [{"action": "backward", "extent": "pulse"}],
    "next_cover_validity": [{"signal_id": "health",
        "critical_health_minimum": 35, "maximum_health_loss": 20,
        "max_source_age_ms": 30000}],
    "action_validity": [{"critical_health_minimum": 35,
        "maximum_health_loss": 20, "minimum_ammo": 1,
        "max_current_age_ms": 1000}],
}

class FakePlannerClient:
    def __init__(self, *args, **kwargs): pass
    def initialize(self): return None
    def close(self): return None

class FakePlanner:
    def __init__(self, *args, **kwargs): self.thread_id = "synthetic-thread"
    def start_session(self): return self.thread_id
    def begin_turn(self, *_args, **_kwargs):
        return types.SimpleNamespace(turn_id="synthetic-turn", thread_id=self.thread_id)
    def await_turn(self, handle, _timeout):
        result_handle = types.SimpleNamespace(turn_id=handle.turn_id,
                                              thread_id=self.thread_id)
        return types.SimpleNamespace(answer=action, usage={"input_tokens": 0},
            handle=result_handle, status="completed", answer_eligible=True,
            cancellation_requested=False, error=None)
    def interrupt(self, _handle): return {"status": "not_needed"}

controller.CodexAppServerClient = FakePlannerClient
controller.PersistentPlannerAdapter = FakePlanner
controller.win = lambda value: str(value)
real_popen = subprocess.Popen
def fake_seam_popen(*args, **kwargs):
    env = dict(os.environ, V39_FAKE_X_TRACE=str(WORK / "fake-x-trace.jsonl"),
               PYTHONPATH=SHIM + os.pathsep +
               str(ROOT) + os.pathsep + str(ROOT / "research/doom") + os.pathsep +
               str(ROOT / "research/live_control"))
    kwargs["env"] = env
    process = real_popen(*args, **kwargs)
    if kwargs.get("stderr") == subprocess.PIPE:
        def drain():
            data = process.stderr.read()
            (WORK / "child.stderr").write_text(data, encoding="utf-8")
        threading.Thread(target=drain, daemon=True).start()
    return process
controller.subprocess.Popen = fake_seam_popen

sys.argv = ["map01_overlap_controller_v39.py", "--out", str(OUT),
    "--iterations", "1", "--seed", "990605", "--session-span", "1",
    "--model", "synthetic-model", "--effort", "low",
    "--load-fixture-manifest", str(fixture_path),
    "--measurement-session", "--per-key-input-measurement"]
try:
    controller.main()
except BaseException:
    print(json.dumps({"construction_error": "controller.main failed",
        "out": str(OUT), "child_stderr": (WORK / "child.stderr").read_text()
            if (WORK / "child.stderr").exists() else None}))
    raise

events_path = OUT / "runtime" / "events.jsonl"
rows = [json.loads(line) for line in events_path.read_text().splitlines()]
events = [row.get("event") for row in rows]
x_trace = [json.loads(line) for line in (WORK / "fake-x-trace.jsonl").read_text().splitlines()]
assert "ready" in events and "accepted" in events and "terminal" in events
assert any(row.get("event") == "input_release_transition" for row in rows)
assert any(row.get("event") == "input_admission" for row in rows)
receipts = [row.get("owner_thread_keyup_receipt") for row in rows
            if row.get("event") == "input_release_transition"]
assert receipts and all(type(item) is dict and
                        item.get("physical_key_measurement", {}).get("classification") ==
                        "CONFIRMED_PHYSICAL_UP" for item in receipts)
assert any(row["event"] == 2 for row in x_trace)
assert any(row["event"] == 3 for row in x_trace)
assert x_trace[-1]["down_after"] == []
assert (OUT / "runtime" / "score.json").is_file()
print(json.dumps({"result": "PASS_CONSTRUCTION_SCOPED",
    "out": str(OUT), "events": len(rows),
    "event_types": sorted(set(events)), "key_release_receipts": len(receipts),
    "remaining_fake_server_keys": x_trace[-1]["down_after"],
    "scope": "real controller/session/Executor/backend/owner code; fake game, model, capture and Xlib"},
    sort_keys=True))
