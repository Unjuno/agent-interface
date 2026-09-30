"""No-GUI validation of the exact v1 method before the next allocation."""
import ast
import hashlib
import json
from pathlib import Path

from compiled_gui_interface_v1 import validate


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "runner.py"
tree = ast.parse(RUNNER.read_text())
node = next(item for item in ast.walk(tree)
            if isinstance(item, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "interface"
                    for target in item.targets))
namespace = {"window": 424242, "SURFACE": "issue3311-chromium-unit-v1"}
loads = {item.id for item in ast.walk(node.value)
         if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)}
missing_names = sorted(loads - set(namespace))
assert not missing_names, f"unbound interface expression names: {missing_names}"
candidate = eval(compile(ast.Expression(node.value), str(RUNNER), "eval"), namespace)
validated = validate(candidate)
assert validated["method"]["max_runtime_ms"] <= 10_000
assert validated["method"]["max_transitions"] == 2
assert validated["method"]["states"]["confirming"]["branches"][0]["when"]["page_state"] == "CONFIRMING"
print(json.dumps({
    "schema": "issue3311_live_interface_preflight_v1",
    "status": "PASS_NO_GUI_INTERFACE_CONTRACT",
    "runner_sha256": hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
    "interface_id": validated["interface_id"],
    "max_runtime_ms": validated["method"]["max_runtime_ms"],
    "max_transitions": validated["method"]["max_transitions"],
    "gui_started": False,
    "model_calls": 0
}, sort_keys=True))
