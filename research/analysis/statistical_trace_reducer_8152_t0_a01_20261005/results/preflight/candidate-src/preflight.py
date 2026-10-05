#!/usr/bin/env python3
"""Role-specific read-only source / isolated writable-output mount check."""
import json
import os
import sys


role = sys.argv[1]
checks = {}
if role == "candidate":
    checks["candidate_source_present"] = os.path.isfile("/src/candidate.py")
    checks["protocol_present"] = os.path.isfile("/src/protocol.json")
    checks["auditor_hidden"] = not os.path.exists("/src/auditor.py")
    checks["prior_raw_hidden"] = not os.path.exists("/in/candidate.raw.json")
    protected = "/src/candidate.py"
else:
    checks["auditor_source_present"] = os.path.isfile("/src/auditor.py")
    checks["protocol_present"] = os.path.isfile("/src/protocol.json")
    checks["candidate_hidden"] = not os.path.exists("/src/candidate.py")
    checks["raw_present"] = os.path.isfile("/in/candidate.raw.json")
    protected = "/src/auditor.py"
try:
    with open(protected, "a", encoding="utf-8"):
        checks["source_write_rejected"] = False
except OSError:
    checks["source_write_rejected"] = True
try:
    with open("/out/mount-preflight.txt", "w", encoding="utf-8") as f:
        f.write(role + " output writable\n")
    checks["output_writable"] = True
except OSError:
    checks["output_writable"] = False
print(json.dumps({"role": role, "checks": checks}, sort_keys=True))
raise SystemExit(0 if checks and all(checks.values()) else 1)
