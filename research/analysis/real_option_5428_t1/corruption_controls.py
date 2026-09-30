#!/usr/bin/env python3
"""Verify the independent auditor rejects four altered copies of the raw run."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
raw = json.loads((root / "raw/formal.json").read_text(encoding="utf-8"))


def corrupt_gate(report):
    row = next(r for r in report["runs"] if not r["gate_open"])
    row["option_aware"]["action"] = "PRIMARY"


def corrupt_regret(report):
    report["runs"][0]["option_aware"]["regret"] = {"n": 999, "d": 1}


def corrupt_route_loss(report):
    report["runs"][0]["option_probe_induced_primary_deadline_loss"] ^= 1


mutations = {
    "missing_factorial_cell": lambda value: value["runs"].pop(),
    "closed_gate_primary_commit": corrupt_gate,
    "forged_regret": corrupt_regret,
    "forged_deadline_loss": corrupt_route_loss,
}
results = {}
with tempfile.TemporaryDirectory(prefix="issue-5428-t1-corruption-") as temp:
    for name, mutate in mutations.items():
        altered = copy.deepcopy(raw)
        mutate(altered)
        path = Path(temp) / f"{name}.json"
        path.write_text(json.dumps(altered), encoding="utf-8")
        run = subprocess.run([sys.executable, str(root / "audit.py"), str(path)],
                             capture_output=True, text=True, check=False)
        try:
            parsed = json.loads(run.stdout)
        except json.JSONDecodeError:
            parsed = {"audit": "INVALID_OUTPUT", "errors": [run.stderr[-500:]]}
        results[name] = {"rejected": parsed.get("audit") == "FAIL",
                         "errors": parsed.get("errors", [])[:8]}
print(json.dumps({"controls": results,
                  "rejected": sum(result["rejected"] for result in results.values()),
                  "total": len(results)}, sort_keys=True, indent=2))
sys.exit(0 if all(result["rejected"] for result in results.values()) else 1)
