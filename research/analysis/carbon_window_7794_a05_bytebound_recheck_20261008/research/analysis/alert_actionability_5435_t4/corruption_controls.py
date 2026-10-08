#!/usr/bin/env python3
"""Confirm the independent replay auditor rejects four corrupted T4 reports."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
formal = json.loads((root / "raw/formal.json").read_text(encoding="utf-8"))


def forged_hard_suppression(report):
    policy = report["streams"][0]["policies"][-1]
    policy["suppressed_ids"].append("s1-first")


def forged_score(report):
    shifted = next(row for row in report["streams"] if row["score_condition"] == "shifted")
    shifted["events"][7]["score"] = 0.8


def forged_miss(report):
    policy = report["streams"][0]["policies"][-1]
    policy["actionable_missed_entities"].clear()


mutations = {
    "missing_factorial_stream": lambda value: value["streams"].pop(),
    "hard_alert_suppression": forged_hard_suppression,
    "shifted_score_rewrite": forged_score,
    "forged_actionable_miss_metric": forged_miss,
}
outcomes = {}
with tempfile.TemporaryDirectory(prefix="issue-5435-t4-corruption-") as temp:
    for name, mutate in mutations.items():
        changed = copy.deepcopy(formal)
        mutate(changed)
        path = Path(temp) / f"{name}.json"
        path.write_text(json.dumps(changed), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(root / "audit.py"), str(path)],
                              capture_output=True, text=True, check=False)
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            report = {"audit": "INVALID_OUTPUT", "errors": [proc.stderr[-500:]]}
        outcomes[name] = {"rejected": report.get("audit") == "FAIL",
                          "errors": report.get("errors", [])[:6]}
print(json.dumps({"controls": outcomes,
                  "rejected": sum(value["rejected"] for value in outcomes.values()),
                  "total": len(outcomes)}, indent=2, sort_keys=True))
sys.exit(0 if all(value["rejected"] for value in outcomes.values()) else 1)
