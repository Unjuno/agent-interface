#!/usr/bin/env python3
"""Exercise the independent auditor against four mutated copies of retained raw."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
raw = json.loads((root / "raw/formal.json").read_text(encoding="utf-8"))
mutations = {
    "wrong_threshold": lambda value: value.update(threshold="3"),
    "missing_dependence_row": lambda value: value["rho_values"].pop(),
    "alter_exact_probability": lambda value: value["rho_values"][0]["false_commit_probability"].update(
        posthoc_max_branch_anytime="1/2"),
    "alter_decimal_probability": lambda value: value["rho_values"][1]["false_commit_decimal"].update(
        fixed_A_anytime=0.75),
}
results = {}
with tempfile.TemporaryDirectory(prefix="issue-5446-t5-corruption-") as temp:
    for name, mutate in mutations.items():
        altered = copy.deepcopy(raw)
        mutate(altered)
        path = Path(temp) / f"{name}.json"
        path.write_text(json.dumps(altered), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(root / "audit.py"), str(path)],
            capture_output=True, text=True, check=False,
        )
        try:
            audit = json.loads(result.stdout)
        except json.JSONDecodeError:
            audit = {"audit": "INVALID_OUTPUT", "errors": [result.stderr[-500:]]}
        results[name] = {"rejected": result.returncode != 0 and audit.get("audit") == "FAIL",
                         "audit": audit}

print(json.dumps({"controls": results,
                  "passed": sum(item["rejected"] for item in results.values()),
                  "total": len(results)}, indent=2, sort_keys=True))
sys.exit(0 if all(item["rejected"] for item in results.values()) else 1)
