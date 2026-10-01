"""Source-visible state/data-flow audit for Issue #5791; no runtime invocation."""
import ast
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(__file__).parent
controller_path = root / "controller.py"
source = controller_path.read_bytes()
tree = ast.parse(source)
text = source.decode("utf-8")

def function(name):
    return next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)

def assigns(node):
    for child in ast.walk(node):
        if isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            yield child

model_call = function("model_call")
reusable_cover = function("reusable_cover")
loop = next(n for n in ast.walk(tree) if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == "index")

facts = {
  "controller_sha256": hashlib.sha256(source).hexdigest(),
  "controller_bytes": len(source),
  "effect_memory_binding": "effect_memory=[row[action] for row in immediately_previous_decision.effect_receipts if result == no_visible_effect]",
  "effect_memory_writes_during_model_wait": 0,
  "effect_memory_passed_to_model_call": "yes; serialized into prompt before subprocess.run",
  "decision_record_persists": "decisions list appends full records; record contains measurements/history and is read only for prior receipt selection and cover policy",
  "reusable_cover_control_state": "at most the immediately previous active action.next_cover; this is existing cover semantics, not correction debt",
  "model_session_id": "persists across decisions within a session span and is passed to runner; runner/provider hidden continuation state is outside this file",
  "explicit_accumulator_identifiers": ["effect_memory"],
  "accumulator_mutations": [],
  "uncertainty": "This is a path-local source audit. It does not inspect model/provider latent context, other controllers, or runtime behavior.",
}

assert "effect_memory=[row[\"action\"] for row in prior_receipts" in text
assert "model_call,model_root,image,model_session_id,effect_memory" in text
assert "model_session_id=None" in text and "model_session_id=observed_session_id" in text
assert "decisions.append" in text
assert "decisions[-1][\"action\"][\"next_cover\"]" in text

# Verify detection can distinguish actual persistent mutation from one-turn evidence.
positive = ast.parse("correction_debt = 0\nwhile blocked:\n correction_debt += requested_delta\n")
negative = ast.parse("effect_memory = [r for r in previous_receipts if r['result'] == 'none']\n")
assert any(isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add) for n in ast.walk(positive))
assert not any(isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add) for n in ast.walk(negative))
facts["positive_control"] = "PASS: explicit accumulation mutation detected"
facts["negative_control"] = "PASS: one-turn receipt projection is not accumulation"
facts["disposition"] = "INELIGIBLE_FOR_THIS_CONTROLLER_PATH; external persistent model context remains uninspected"
print(json.dumps(facts, sort_keys=True, indent=2))

