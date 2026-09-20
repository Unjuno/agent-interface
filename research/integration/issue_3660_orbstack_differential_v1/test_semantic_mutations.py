#!/usr/bin/env python3
"""Independent semantic mutation controls without editing the frozen test bundle."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from audit_raw import audit


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "evidence/frozen_3652_formal01_raw.json"
PREDECESSOR = ROOT / "evidence/predecessor_audit_readback.py"


def reseal(raw):
    for index, event in enumerate(raw["ledger"]):
        event["seq"] = index
        body = dict(event)
        body.pop("hash", None)
        event["hash"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    raw["event_count"] = len(raw["ledger"])
    return raw


def main():
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    cases = {"untouched": copy.deepcopy(raw)}

    focus = copy.deepcopy(raw)
    next(event for event in focus["ledger"] if event["kind"] == "focus_drift")["active"] = raw["apps"]["calc"]["window"]
    cases["focus_active_wrong_resealed"] = reseal(focus)

    modal = copy.deepcopy(raw)
    next(event for event in modal["ledger"] if event["kind"] == "modal_transition")["parent"] = raw["apps"]["inkscape"]["window"]
    cases["modal_parent_wrong_resealed"] = reseal(modal)

    expected = {
        "untouched": "HOLD_AUDIT_EVIDENCE_INCOMPLETE",
        "focus_active_wrong_resealed": "FAIL_AUDIT_INTEGRITY",
        "modal_parent_wrong_resealed": "FAIL_AUDIT_INTEGRITY",
    }
    results = {name: audit(value) for name, value in cases.items()}
    failures = [name for name, result in results.items() if result["decision"] != expected[name]]

    predecessor_results = {}
    mutant_hashes = {}
    with tempfile.TemporaryDirectory(prefix="issue3660-semantic-mutations-") as temp:
        temp_path = Path(temp)
        for name, value in cases.items():
            payload = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
            mutant_path = temp_path / f"{name}.json"
            mutant_path.write_bytes(payload)
            mutant_hashes[name] = hashlib.sha256(payload).hexdigest()
            proc = subprocess.run([sys.executable, str(PREDECESSOR), str(mutant_path)],
                                 capture_output=True, text=True, check=False)
            try:
                old_result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                old_result = {"decision": "NO_JSON_RECEIPT", "stderr": proc.stderr[-1000:]}
            predecessor_results[name] = {
                "exit_code": proc.returncode,
                "decision": old_result.get("decision"),
                "errors": old_result.get("errors", []),
            }

    receipt = {
        "decision": "PASS_SEMANTIC_MUTATION_CONTROLS" if not failures else "FAIL_MUTATION_ACCEPTED",
        "frozen_raw_sha256": hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(),
        "expected": expected,
        "results": {name: {"decision": result["decision"], "errors": result["errors"], "gaps": result["gaps"]}
                    for name, result in results.items()},
        "mutant_sha256": mutant_hashes,
        "predecessor_audit_replay": predecessor_results,
        "failures": failures,
    }
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
