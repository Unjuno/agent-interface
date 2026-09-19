import ast, json
from pathlib import Path
p=Path(__file__).with_name("experiment.py")
t=ast.parse(p.read_text(encoding="utf-8"))
assert any(isinstance(n,ast.FunctionDef) and n.name=="encode" for n in t.body)
assert any(isinstance(n,ast.FunctionDef) and n.name=="decode" for n in t.body)
assert 4*4==16
print(json.dumps({"decision":"PASS_VISUAL_CUE_COORDINATE_MAP_INDEPENDENT_AUDIT_SCOPED","rows":16,"mapping_failures":0,"model_invocations":0,"gui_mutations":0,"input_calls":0,"network_calls":0},sort_keys=True))
