from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
A1 = ROOT / "research/doom/v39_soft_feedback_routing_a01_20261005"
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"
A1_RESULT = A1 / "RESULT.json"
FREEZE = json.loads((PKG / "FREEZE.json").read_text(encoding="utf-8"))

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

for name, path in (("controller", CONTROLLER), ("a01_result", A1_RESULT),
                   ("candidate", PKG / "candidate.py")):
    if digest(path) != FREEZE["sha256"][name]:
        raise RuntimeError(f"frozen {name} hash mismatch")

raw = json.loads(A1_RESULT.read_text(encoding="utf-8"))
event = raw["monitor"]["latest_soft_event"]
source = CONTROLLER.read_text(encoding="utf-8")
tree = ast.parse(source)
wanted = {"latest_soft_event_summary", "begin_model_turn"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
if {node.name for node in nodes} != wanted:
    raise RuntimeError("required V39 helpers missing")
namespace = {"json": json}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(CONTROLLER), "exec"), namespace)

prior_decision = {
    "iteration": 0,
    "cover_policy_source_iteration": 0,
    "cover_validity_soft_events": raw["monitor"]["soft_event_count"],
    "cover_validity_latest_soft_event": event,
}
summary = namespace["latest_soft_event_summary"]([prior_decision])

class StubPlanner:
    def __init__(self):
        self.prompts = []
        self.calls = []
    def begin_turn(self, prompt_text, **kwargs):
        self.calls.append("begin_turn")
        self.prompts.append(prompt_text)
        return {"turn_id": "stub-turn-2"}

planner = StubPlanner()
namespace["win"] = lambda path: str(path)
with TemporaryDirectory(prefix="v39-soft-route-a03-") as temporary:
    temp = Path(temporary)
    namespace["begin_model_turn"](
        planner, temp, temp / "synthetic.png", [], 100, 37, summary, {"type": "object"})
    prompt = planner.prompts[0]

expected_json = json.dumps(summary, separators=(",", ":"))
result = {
    "schema": "v39-soft-next-turn-delivery-result-a03-v1",
    "main_base": FREEZE["main_base"],
    "candidate_sha256": digest(PKG / "candidate.py"),
    "a01_result_sha256": digest(A1_RESULT),
    "controller_sha256": digest(CONTROLLER),
    "summary": summary,
    "planner": {"calls": planner.calls, "prompt": prompt,
                "prompt_contains_exact_summary": expected_json in prompt,
                "current_health": 100, "current_ammo": 37},
    "scope": "one offline next-turn prompt-builder construction with stub planner; no model/game/input/live allocation",
}
(PKG / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"candidate": "completed", "calls": planner.calls,
                  "exact_summary_in_prompt": expected_json in prompt,
                  "summary": summary}, sort_keys=True))
