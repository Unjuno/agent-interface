#!/usr/bin/env python3
"""Confirm the raw trace auditor rejects four altered copies of the report."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
raw = json.loads((root / "raw/formal.json").read_text(encoding="utf-8"))
mutations = {
    "missing_policy_run": lambda value: value["runs"].pop(),
    "forged_terminal_deadlock": lambda value: value["runs"][0].update(unrecovered_deadlock=False),
    "resource_owner_corruption": lambda value: value["runs"][0]["trace"][0].update(resource="Z"),
    "false_completion_count": lambda value: value["runs"][0].update(completed_workflows=99),
}
results = {}
with tempfile.TemporaryDirectory(prefix="issue-5410-t0-corruption-") as temp:
    for name, mutate in mutations.items():
        changed = copy.deepcopy(raw)
        mutate(changed)
        path = Path(temp) / f"{name}.json"
        path.write_text(json.dumps(changed), encoding="utf-8")
        result = subprocess.run([sys.executable, str(root / "audit.py"), str(path)],
                                capture_output=True, text=True, check=False)
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
