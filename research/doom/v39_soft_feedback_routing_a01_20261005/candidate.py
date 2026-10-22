from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
FREEZE = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"
GUARD = PKG / "source/observable_signal_guard_v2.py"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_pin(name: str, path: Path) -> None:
    expected = FREEZE["sha256"][name]
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"frozen {name} SHA-256 mismatch: {actual}")

if FREEZE["main_base"] != "f60752d0fb71595363a80977636ca74c1fd10b21":
    raise RuntimeError("wrong main base")
check_pin("controller", CONTROLLER)
check_pin("guard_source_copy", GUARD)
if sha256(PKG / "candidate.py") != FREEZE["sha256"]["candidate"]:
    raise RuntimeError("candidate SHA-256 mismatch")

spec = importlib.util.spec_from_file_location("frozen_observable_signal_guard_v2", GUARD)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load frozen production guard")
guard_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard_module)
source = CONTROLLER.read_text(encoding="utf-8")
tree = ast.parse(source)
wanted = {
    "_typed_json_equal", "_signal_pair_matches", "_signal_pair_content_matches",
    "guard_spec", "ammo_guard_spec", "DoomCoverSignalPairMonitor",
    "begin_model_turn",
}
nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
         and node.name in wanted]
if {node.name for node in nodes} != wanted:
    raise RuntimeError("required current V39 AST nodes missing")
namespace = {"json": json, "time": time,
             "ObservableSignalGuard": guard_module.ObservableSignalGuard}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(CONTROLLER), "exec"), namespace)

source_binding = {"surface": "offline-synthetic", "source": "A01"}
def signal(signal_id: str, value: int, sequence: int, capture_ns: int) -> dict:
    return {"status": "observed", "signal_id": signal_id, "value": value,
            "sequence": sequence, "capture_ns": capture_ns,
            "binding": dict(source_binding)}

health0 = signal("health", 100, 1, 1_000_000_000)
ammo0 = signal("ammo", 46, 1, 1_000_000_000)
validity = {"critical_health_minimum": 35, "maximum_health_loss": 12,
            "max_source_age_ms": 30000}
hspec = namespace["guard_spec"](validity, health0, 0)
aspec = namespace["ammo_guard_spec"](ammo0, 0, 30000)
guards = {
    "health": guard_module.ObservableSignalGuard(hspec, health0, source_binding),
    "ammo": guard_module.ObservableSignalGuard(aspec, ammo0, source_binding),
}
class Reader:
    def read(self, observation):
        raise AssertionError("typed-observation path must not call image reader")
monitor = namespace["DoomCoverSignalPairMonitor"](guards, Reader(), Reader())

class StubPlanner:
    def __init__(self):
        self.prompts = []
        self.calls = []
    def begin_turn(self, prompt_text, **kwargs):
        self.calls.append("begin_turn")
        self.prompts.append(prompt_text)
        return {"turn_id": "stub-turn-1"}

planner = StubPlanner()
with TemporaryDirectory(prefix="v39-soft-route-a01-") as temporary:
    temp = Path(temporary)
    (temp / "source.png").write_bytes(b"synthetic-stub-image")
    begin_model_turn = namespace["begin_model_turn"]
    namespace["win"] = lambda path: str(path)
    begin_model_turn(planner, temp, temp / "source.png", [], 100, 46, None,
                     {"type": "object"})
    prompt_before = planner.prompts[0]
    observation = {
        "event": "typed_observation", "sequence": 2,
        "capture_ns": 2_000_000_000, "pointer_binding": dict(source_binding),
        "frame_rgb_sha256": "a" * 64,
        "signals": {"health": signal("health", 100, 2, 2_000_000_000),
                    "ammo": signal("ammo", 37, 2, 2_000_000_000)},
    }
    monitor_output = monitor.observe(observation)
    prompt_after = planner.prompts[0]

result = {
    "schema": "v39-soft-event-routing-result-a01-v1",
    "main_base": FREEZE["main_base"],
    "candidate_sha256": sha256(PKG / "candidate.py"),
    "source_sha256": {"controller": sha256(CONTROLLER), "guard_source_copy": sha256(GUARD)},
    "input": {"health": [100, 100], "ammo": [46, 37],
              "sequence": [1, 2], "capture_ns": [1_000_000_000, 2_000_000_000],
              "binding_unchanged": True, "frame_hash_changed": True,
              "health_hard_minimum": hspec["hard_minimum"],
              "ammo_hard_minimum": aspec["hard_minimum"]},
    "monitor": {"returned": monitor_output, "soft_event_count": monitor.soft_event_count,
                "latest_soft_event": monitor.latest_soft_event,
                "policy_invalidation": monitor_output is not None},
    "pending_planner_stub": {"calls": planner.calls, "prompt_before": prompt_before,
                              "prompt_after": prompt_after,
                              "prompt_unchanged_after_observation": prompt_before == prompt_after},
    "scope": "one offline synthetic typed-observation/source-composition probe; no model, game, GUI, OS input, container, or live allocation",
}
(PKG / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"candidate": "completed", "result": str(PKG / "RESULT.json"),
                  "monitor_returned": monitor_output,
                  "soft_event_count": monitor.soft_event_count,
                  "planner_calls": planner.calls}, sort_keys=True))
