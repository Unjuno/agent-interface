"""Successor-allocation runner for the changed-goal positive control."""
import json
import sys

from candidate import run

fixture = json.load(sys.stdin)
case = fixture["case"]
print(json.dumps({case["id"]: run(case)}, sort_keys=True, separators=(",", ":")))
