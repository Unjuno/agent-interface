import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = Path(__file__).resolve().parent
CONTROLLER = ROOT / "research/doom/map01_overlap_controller_v39.py"
RESULT = json.loads((PKG / "RESULT.json").read_text(encoding="utf-8"))
source_bytes = CONTROLLER.read_bytes()
source_sha = hashlib.sha256(source_bytes).hexdigest()
source = source_bytes.decode("utf-8")
tree = ast.parse(source)
main = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main")
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
continue_nodes = [child for child in ast.walk(invalidation_if)
                  if isinstance(child, ast.Continue)]
calls = [(node.lineno, node.func.id) for node in ast.walk(main)
         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
         and node.func.id in {"latest_soft_event_summary", "begin_model_turn"}]
summary_line = next(line for line, name in calls if name == "latest_soft_event_summary")
prompt_line = next(line for line, name in calls if name == "begin_model_turn")
summary = RESULT["summary_after_cancel"]
prompt = RESULT["stub_next_prompt"]
summary_text = next(
    line.split(": ", 1)[1]
    for line in RESULT["stub_next_prompt"].splitlines()
    if line.startswith("Newest typed soft event from the preceding control interval: "))
prompt_summary = json.loads(summary_text)
checks = {
    "main_identity": RESULT["main_base"] == "018934cdf45fcabffcc4efe25b5c7b3d59bd459f",
    "controller_hash_matches_candidate": RESULT["controller_sha256"] == source_sha,
    "invalidation_branch_contains_event_count_and_latest_event": {
        "cover_validity_soft_events", "cover_validity_latest_soft_event"}.issubset(event_fields),
    "decision_append_precedes_continue": bool(continue_nodes)
        and append.lineno < min(node.lineno for node in continue_nodes),
    "next_loop_summary_precedes_prompt_builder": summary_line < prompt_line,
    "helper_summary_structurally_matches_stub_prompt": prompt_summary == summary,
    "summary_preserves_no_authority": summary.get("grants_input_authority") is False,
    "candidate_raw_source_lines_match": RESULT["source"]["decision_append_line"] == append.lineno
        and RESULT["source"]["invalidation_branch_line"] == invalidation_if.lineno,
}
audit = {
    "schema": "v39-soft-feedback-a05-cancel-carry-audit-v2",
    "checks": checks,
    "disposition": "PASS_SCOPED_CANCEL_CARRY" if all(checks.values()) else "FAIL",
    "scope": "independent source/raw consistency audit; no runtime/model/game/input or live allocation",
}
(PKG / "audit_successor_A02.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(audit, sort_keys=True))
if not all(checks.values()):
    raise SystemExit(1)
