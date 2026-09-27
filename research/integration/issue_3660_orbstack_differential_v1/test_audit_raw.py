#!/usr/bin/env python3
"""Mutation controls for the independent raw-only auditor; no GUI/input."""
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from audit_raw import audit


def seal(raw):
    for i, event in enumerate(raw["ledger"]):
        event["seq"] = i
        body = dict(event)
        body.pop("hash", None)
        event["hash"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    raw["event_count"] = len(raw["ledger"])
    return raw


raw = json.loads(Path(sys.argv[1]).read_text())
cases = {"untouched": copy.deepcopy(raw)}

runner_flags = copy.deepcopy(raw)
runner_flags["checks"] = [False, False, False, False, False]
cases["runner_booleans_false"] = runner_flags

reordered = copy.deepcopy(raw)
reordered["ledger"][4], reordered["ledger"][5] = reordered["ledger"][5], reordered["ledger"][4]
cases["reordered_events_resealed"] = seal(reordered)

extra = copy.deepcopy(raw)
extra["ledger"].insert(4, {"kind": "unregistered_transition", "seq": 0})
cases["extra_event_resealed"] = seal(extra)

for name, count in (("input_count_low", 2), ("input_count_high", 4), ("input_count_bool", True)):
    changed = copy.deepcopy(raw)
    changed["input_operations"] = count
    cases[name] = changed

identity = copy.deepcopy(raw)
identity["apps"]["chromium"]["identity"]["matches"][0]["window"] = "999"
cases["role_identity_mutation"] = identity

stale = copy.deepcopy(raw)
next(e for e in stale["ledger"] if e["kind"] == "stale_window_admission")["disposition"] = "accepted"
cases["stale_identity_accepted"] = seal(stale)

cleanup = copy.deepcopy(raw)
cleanup["ledger"][-1]["processes"][0]["remaining_pids"] = [99999]
cleanup["cleanup_processes"][0]["remaining_pids"] = [99999]
cases["cleanup_survivor_mutation"] = seal(cleanup)

results = {name: audit(value) for name, value in cases.items()}
expected = {"untouched": "HOLD_AUDIT_EVIDENCE_INCOMPLETE"}
expected["runner_booleans_false"] = "HOLD_AUDIT_EVIDENCE_INCOMPLETE"
for name in cases.keys() - expected.keys():
    expected[name] = "FAIL_AUDIT_INTEGRITY"
failures = [name for name, result in results.items() if result["decision"] != expected[name]]
receipt = {"decision": "PASS_MUTATION_CONTROLS" if not failures else "FAIL_MUTATION_ACCEPTED",
           "expected": expected,
           "results": {name: {"decision": value["decision"], "errors": value["errors"], "gaps": value["gaps"]}
                       for name, value in results.items()},
           "failures": failures}
out = Path(os.environ.get("MUTATION_OUTPUT", "/tmp/mutations"))
out.mkdir(parents=True, exist_ok=True)
manifest = {}
for name, value in cases.items():
    payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    (out / f"{name}.json").write_bytes(payload)
    manifest[name] = hashlib.sha256(payload).hexdigest()
predecessor = Path(os.environ["PREDECESSOR_AUDIT"])
predecessor_replay = {}
for name in cases:
    proc = subprocess.run([sys.executable, str(predecessor), str(out / f"{name}.json")],
                          text=True, capture_output=True, check=False)
    try:
        old_result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        old_result = {"decision": "NO_JSON_RECEIPT", "stderr": proc.stderr[-1000:]}
    predecessor_replay[name] = {"exit_code": proc.returncode, "decision": old_result.get("decision"),
                                "errors": old_result.get("errors", [])}
receipt["mutant_sha256"] = manifest
receipt["predecessor_audit_replay"] = predecessor_replay
(out / "mutation-tests.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print(json.dumps(receipt, sort_keys=True, indent=2))
if failures:
    raise SystemExit(1)
