"""Deterministic positive/negative-control candidate for the frozen source audit."""
import ast
import hashlib
import json
import pathlib

p = pathlib.Path(__file__).with_name("controller.py")
t = p.read_text(encoding="utf-8")
tree = ast.parse(t)
positive = ast.parse("debt=0\nwhile blocked:\n debt += delta\n")
negative = ast.parse("memory=[r for r in receipts if r['result']=='none']\n")
assert any(isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add) for n in ast.walk(positive))
assert not any(isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add) for n in ast.walk(negative))
assert 'effect_memory=[row["action"] for row in prior_receipts' in t
assert "model_call,model_root,image,model_session_id,effect_memory" in t
assert "model_session_id=observed_session_id" in t
print(json.dumps({"controller_sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "positive_control": "PASS", "negative_control": "PASS", "candidate": "INELIGIBLE_FOR_THIS_CONTROLLER_PATH", "external_persistent_model_context": "UNINSPECTED"}, sort_keys=True))
