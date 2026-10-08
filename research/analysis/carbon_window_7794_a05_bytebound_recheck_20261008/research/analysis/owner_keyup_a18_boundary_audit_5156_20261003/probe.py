"""Construction diagnosis; does not rerun A18's candidate or formal auditor CLI."""
import importlib.util
import json
from pathlib import Path
from mutations import cases

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a18_retained", HERE / "retained" / "audit.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
raw = json.loads((HERE / "retained" / "raw.json").read_text())
rows = []
for name, item, invalid in cases(raw):
    try:
        errors = module.audit(item)
        rows.append({"case": name, "invalid": invalid, "accepted": not errors, "errors": errors})
    except Exception as exc:
        rows.append({"case": name, "invalid": invalid, "exception": type(exc).__name__ + ": " + str(exc)})
print(json.dumps(rows, indent=2))
