"""Independent checks of pinned receipt inputs and the retained construction result."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOOM = ROOT.parent


def audit():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    for pin in [freeze["tail_validator"], *freeze["dependencies"]]:
        path = DOOM / Path(pin["path"]).name
        payload = path.read_bytes() if path.is_file() else b""
        blob = subprocess.run(["git", "hash-object", str(path)], capture_output=True,
                              text=True).stdout.strip() if path.is_file() else None
        if blob != pin["git_blob"] or hashlib.sha256(payload).hexdigest() != pin["sha256"]:
            errors.append("source_pin:" + pin["path"])

    for item in freeze["event_inputs"]:
        raw = subprocess.run(["git", "cat-file", "blob", item["git_blob"]],
                             capture_output=True, check=False).stdout
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            errors.append("event_input:" + item["cell"])
        try:
            events = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
            receipts = [row for row in events if row.get("event") == "input_release_transition"
                        and row.get("key") == "d"]
            expected_count = 2 if item["cell"] in ("01-pulse", "02-pulse", "05-pulse") else 0
            if len(receipts) != expected_count:
                errors.append("receipt_count:" + item["cell"])
        except (UnicodeDecodeError, json.JSONDecodeError):
            errors.append("event_parse:" + item["cell"])

    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    if (result.get("retained_d_keyup_receipts") != 6 or
            result.get("verified_receipts_accepted") != 6 or
            result.get("scorer_samples_taken") != 0 or
            result.get("result") != "RECEIPT_SHAPE_COMPATIBLE_ZERO_SAMPLES" or
            len(result.get("receipts", [])) != 6):
        errors.append("result_contract")
    if any(row.get("tail_samples") != 0 or row.get("termination") != "deadline"
           or row.get("tail_disposition") != "CENSORED"
           for row in result.get("receipts", [])):
        errors.append("zero_sample_censoring")
    actual_rows = [(row.get("cell"), row.get("step"), row.get("key"))
                   for row in result.get("receipts", [])]
    expected_rows = [(cell, step, "d")
                     for cell in ("01-pulse", "02-pulse", "05-pulse")
                     for step in (0, 2)]
    if sorted(actual_rows) != sorted(expected_rows):
        errors.append("receipt_identity_accounting")

    audit_result = {
        "schema": "map01-scorer-tail-receipt-construction-audit-v1",
        "pass": not errors,
        "errors": errors,
        "cells": len(freeze["event_inputs"]),
        "receipt_count": result.get("retained_d_keyup_receipts"),
        "scope": "input hashes, real receipt presence, and zero-sample result accounting; no runtime integration audit",
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(audit_result, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8")
    return audit_result


if __name__ == "__main__":
    outcome = audit()
    print(json.dumps(outcome, indent=2, sort_keys=True))
    raise SystemExit(0 if outcome["pass"] else 1)
