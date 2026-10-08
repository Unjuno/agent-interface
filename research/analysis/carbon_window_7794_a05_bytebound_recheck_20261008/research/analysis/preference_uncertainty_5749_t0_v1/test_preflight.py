import importlib.util
import json
from pathlib import Path

root = Path(__file__).parent
for name in ("runner", "audit"):
    spec = importlib.util.spec_from_file_location(name, root / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    globals()[name] = module
fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
doc = runner.build_raw()
result = audit.audit(doc)
assert result["errors"] == [], result
assert len(audit.corruption_suite(doc)) == 7
assert all(row["rejected"] for row in audit.corruption_suite(doc))
print("PREFLIGHT_PASS", result)
