"""Invoke the unchanged A03 one-pair consumer once on the frozen four rows."""
import importlib.util
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005" / "candidate.py"
spec = importlib.util.spec_from_file_location("baseline_a03_consumer", BASELINE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rows = [json.loads(x) for x in (HERE / "INPUT_EVENTS.jsonl").read_text().splitlines() if x]
freeze = json.loads((HERE / "FREEZE.json").read_text())
if hashlib.sha256((HERE / "INPUT_EVENTS.jsonl").read_bytes()).hexdigest() != freeze["source_input_sha256"]:
    raise SystemExit("frozen input hash mismatch")
if hashlib.sha256(BASELINE.read_bytes()).hexdigest() != freeze["source_sha256"]["baseline_A03_candidate.py"]:
    raise SystemExit("baseline source hash mismatch")
try:
    result = {"disposition": "UNEXPECTED_ACCEPT", "value": module.reconstruct(rows)}
except Exception as exc:
    result = {"disposition": "FAIL_CLOSED_AS_EXPECTED", "exception_type": type(exc).__name__,
              "message": str(exc), "input_event_count": len(rows)}
path = HERE / "results" / "a01" / "BASELINE.json"
path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(json.dumps(result, sort_keys=True))
if result["disposition"] != "FAIL_CLOSED_AS_EXPECTED":
    raise SystemExit(1)
