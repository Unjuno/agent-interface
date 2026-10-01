import ast
from pathlib import Path


source = Path(__file__).with_name("audit.py").read_text(encoding="utf-8")
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "independent_closure")
scope = {}
exec(compile(ast.Module(body=[function], type_ignores=[]), "audit.py", "exec"), scope)
closure = scope["independent_closure"]

ordinary = {"decision": {"edges": [{"to": "freshness", "kind": "invalidation"}]},
            "freshness": {"value": True, "edges": []}}
assert closure(ordinary) == ["decision", "freshness"]

unresolved = {"decision": {"edges": [{"to": "external_cause", "kind": "unknown"}]}}
assert closure(unresolved) == ["decision", "external_cause"]
assert "external_cause" not in unresolved

filtered = closure(unresolved, {"data"})
assert filtered == ["decision"]
print("CONSTRUCTION_PASS: ordinary closure and unresolved external sentinel")
