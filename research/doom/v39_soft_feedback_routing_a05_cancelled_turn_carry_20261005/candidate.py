import ast
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"
EXPECTED_MAIN = "018934cdf45fcabffcc4efe25b5c7b3d59bd459f"
EXPECTED_SHA = "4548ca30b5a962946c7f81a58784a5b8e672a10635f4737c36b38f596b2c27ca"

source_bytes = CONTROLLER.read_bytes()
source_sha = hashlib.sha256(source_bytes).hexdigest()
if source_sha != EXPECTED_SHA:
    raise RuntimeError(f"controller source changed: {source_sha}")
source = source_bytes.decode("utf-8")
tree = ast.parse(source)
main = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main")
lines = source.splitlines()

invalidation_if = next(node for node in ast.walk(main)
                       if isinstance(node, ast.If)
                       and ast.get_source_segment(source, node.test) == "invalidation is not None")
append = next(node for node in ast.walk(invalidation_if)
              if isinstance(node, ast.Call)
              and isinstance(node.func, ast.Attribute)
              and node.func.attr == "append"
              and any(isinstance(child, ast.Constant)
                      and child.value == "cover_validity_latest_soft_event"
                      for child in ast.walk(node)))
event_fields = {child.value for child in ast.walk(append)
                if isinstance(child, ast.Constant) and isinstance(child.value, str)}
has_continue = any(isinstance(child, ast.Continue) for child in ast.walk(invalidation_if))
main_calls = [(node.lineno, node.func.id) for node in ast.walk(main)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id in {"latest_soft_event_summary", "begin_model_turn"}]
summary_line = next(line for line, name in main_calls if name == "latest_soft_event_summary")
prompt_line = next(line for line, name in main_calls if name == "begin_model_turn")
if not {"cover_validity_soft_events", "cover_validity_latest_soft_event"}.issubset(event_fields):
    raise RuntimeError("invalidation decision does not retain both soft-event fields")
if not has_continue or not summary_line < prompt_line:
    raise RuntimeError("cancel/next-turn source order mismatch")

helpers = {node.name: node for node in tree.body
           if isinstance(node, ast.FunctionDef)
           and node.name in {"latest_soft_event_summary", "begin_model_turn"}}
if set(helpers) != {"latest_soft_event_summary", "begin_model_turn"}:
    raise RuntimeError("required V39 helper missing")
namespace = {"json": json}
exec(compile(ast.Module(body=list(helpers.values()), type_ignores=[]),
             str(CONTROLLER), "exec"), namespace)
event = {
    "sequence": 2,
    "signal": {"signal_id": "ammo", "value": 37, "sequence": 2},
    "outcome": {
        "signal_id": "ammo", "status": "SOFT_CHANGED",
        "reason": "within_validity_envelope", "keep_existing_policy": True,
        "requires_new_decision": False, "grants_input_authority": False,
        "may_only_preserve_or_reduce_existing_authority": True,
        "source_value": 46, "current_value": 37, "hard_minimum": 1,
    },
}
canceled_decision = {
    "iteration": 1,
    "cover_policy_source_iteration": 0,
    "cover_validity_soft_events": 1,
    "cover_validity_latest_soft_event": event,
    "policy_invalidation": {"reason": "health:below_hard_minimum"},
    "model_action_discarded": True,
    "plan_terminal": "not_admitted",
}
summary = namespace["latest_soft_event_summary"]([canceled_decision])

class StubPlanner:
    def __init__(self):
        self.prompts = []

    def begin_turn(self, prompt_text, **kwargs):
        self.prompts.append(prompt_text)
        return {"turn_id": "stub-after-cancel"}

planner = StubPlanner()
namespace["win"] = lambda path: str(path)
with tempfile.TemporaryDirectory(prefix="v39-soft-cancel-carry-") as temp_dir:
    temp = Path(temp_dir)
    namespace["begin_model_turn"](
        planner, temp, temp / "synthetic.png", [], 96, 37, summary, {"type": "object"})
prompt = planner.prompts[0]
summary_json = json.dumps(summary, separators=(",", ":"))
result = {
    "schema": "v39-soft-feedback-a05-cancel-carry-v1",
    "main_base": EXPECTED_MAIN,
    "controller_sha256": source_sha,
    "source": {
        "invalidation_branch_line": invalidation_if.lineno,
        "decision_append_line": append.lineno,
        "soft_event_fields_retained": True,
        "continue_after_append": has_continue,
        "next_summary_call_line": summary_line,
        "next_prompt_builder_call_line": prompt_line,
    },
    "synthetic_canceled_decision": canceled_decision,
    "summary_after_cancel": summary,
    "stub_next_prompt": prompt,
    "prompt_contains_exact_summary": summary_json in prompt,
    "summary_grants_input_authority": summary["grants_input_authority"],
    "scope": "offline current-source AST and helper composition only; no model, game, GUI, OS input, container, or live allocation",
}
(PKG / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps({"candidate": "PASS_SCOPED_CANCEL_CARRY", "result": str(PKG / "RESULT.json"),
                  "event_fields_retained": True, "summary_line": summary_line,
                  "prompt_line": prompt_line, "exact_summary_in_prompt": summary_json in prompt},
                 sort_keys=True))
