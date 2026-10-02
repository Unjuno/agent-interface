#!/usr/bin/env python3
"""Independent raw-only verifier for the retained host construction."""
import hashlib
import json
import pathlib
import sys

RAW_SHA256 = "89a64b887353d6448acdd09fcd6719613fbf1abee7cdf6f44b4d0b5a26f72ed9"
EXPECTED = [
    {"classification":"UNKNOWN_TELEMETRY","projection":{"case_id":"release-gap-01","completeness":{"release":False},"events":[{"generation":3,"kind":"input"}]}},
    {"classification":"UNKNOWN_TELEMETRY","projection":{"case_id":"release-gap-01","completeness":{"release":False},"events":[{"generation":3,"kind":"input"}]}},
    {"classification":"CONFIRMED_COMPLETE","projection":{"case_id":"complete-present","completeness":{"release":True},"events":[{"generation":3,"kind":"input"},{"generation":3,"kind":"release"}]}},
    {"classification":"CONFIRMED_OMISSION","projection":{"case_id":"complete-absent","completeness":{"release":True},"events":[{"generation":3,"kind":"input"}]}},
]

def audit(raw):
    errors = []
    if hashlib.sha256(raw).hexdigest() != RAW_SHA256:
        errors.append("raw_sha256")
    try:
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except Exception:
        return {"audit":"FAIL","errors":["invalid_jsonl"]}
    if rows != EXPECTED:
        errors.append("frozen_rows")
    if len(rows) >= 2:
        if rows[0]["projection"] != rows[1]["projection"]:
            errors.append("world_projection_identity")
        if [rows[0]["classification"], rows[1]["classification"]] != ["UNKNOWN_TELEMETRY", "UNKNOWN_TELEMETRY"]:
            errors.append("world_disposition")
    return {"audit":"PASS_IDENTIFIABILITY_CONSTRUCTION" if not errors else "FAIL","errors":errors,"rawSha256":hashlib.sha256(raw).hexdigest(),"rows":len(rows)}

def main(path):
    raw = pathlib.Path(path).read_bytes()
    result = audit(raw)
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    return 0 if result["audit"] == "PASS_IDENTIFIABILITY_CONSTRUCTION" else 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit.py raw.jsonl")
    raise SystemExit(main(sys.argv[1]))
