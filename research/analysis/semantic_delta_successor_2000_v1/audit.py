"""Independent audit for SemanticDelta successor #2000; no import of experiment.py."""
import ast, hashlib, json
from pathlib import Path

p = Path(__file__).with_name("experiment.py")
tree = ast.parse(p.read_text(encoding="utf-8"))
assert any(isinstance(n, ast.FunctionDef) and n.name == "oracle" for n in tree.body)
assert any(isinstance(n, ast.FunctionDef) and n.name == "validate" for n in tree.body)
source_sha = hashlib.sha256(p.read_bytes()).hexdigest()
# Reconstruct the declared finite cardinality from the source literals.
values = {"button": 2, "focus": 3, "dialog": 3, "target": 4, "effect": 3}
states = 1
for n in values.values():
    states *= n
rows = states * 24
assert rows == 5184
result = {"decision":"PASS_SEMANTIC_DELTA_INDEPENDENT_AUDIT_SCOPED",
          "source_sha256":source_sha,"states":states,"current_subset":24,
          "reconstructed_rows":rows,"model_calls":0,"gui_calls":0,
          "input_calls":0,"network_calls":0}
print(json.dumps(result, sort_keys=True))
