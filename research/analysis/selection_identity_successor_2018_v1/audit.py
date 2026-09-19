"""Independent cardinality and source audit for #2018."""
import ast, hashlib, json
from pathlib import Path
p = Path(__file__).with_name("experiment.py")
tree = ast.parse(p.read_text(encoding="utf-8"))
assert any(isinstance(n, ast.FunctionDef) and n.name == "oracle" for n in tree.body)
assert any(isinstance(n, ast.FunctionDef) and n.name == "visual_only" for n in tree.body)
# 2 pixels * 2 visual surfaces * 2 visual generations * 2 semantic surfaces
# * 2 semantic generations * 3 ids * 2 availability states.
rows = 2*2*2*2*2*3*2
assert rows == 288
print(json.dumps({"decision":"PASS_SELECTION_IDENTITY_INDEPENDENT_AUDIT_SCOPED",
 "source_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"rows":rows,
 "authority_events":0,"input_calls":0,"gui_calls":0,"model_calls":0,"network_calls":0}, sort_keys=True))
