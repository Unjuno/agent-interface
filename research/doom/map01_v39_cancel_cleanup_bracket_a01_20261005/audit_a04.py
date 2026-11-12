"""Independently check preserved owner cleanup measurements in the guard receipt."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results" / "a04"
INPUT = HERE / "results" / "a03" / "candidate-events.jsonl"
GUARD = ROOT / "research" / "live_control" / "running_action_guard_v3.py"


def main():
    errors = []
    freeze = json.loads((HERE / "FREEZE-A04.json").read_text())
    source_map = {"running_action_guard_v3.py": GUARD,
                  "a03_candidate_events.jsonl": INPUT,
                  "run_a04.py": HERE / "run_a04.py",
                  "audit_a04.py": HERE / "audit_a04.py"}
    for name, expected in freeze["sources"].items():
        if hashlib.sha256(source_map[name].read_bytes()).hexdigest() != expected["sha256"]:
            errors.append(f"source hash mismatch: {name}")
    source_rows = [json.loads(line) for line in INPUT.read_text().splitlines() if line]
    expected_cleanup = next(row for row in source_rows if row.get("event") == "owner_release")
    receipt_raw = (OUT / "release-receipt.json").read_bytes()
    receipt = json.loads(receipt_raw)
    result = json.loads((OUT / "RESULT.json").read_text())
    if len(receipt.get("early_releases", [])) != 1:
        errors.append("expected one retained early physical release")
    else:
        event = receipt["early_releases"][0]
        actual_cleanup = event.get("owner_release")
        if actual_cleanup != expected_cleanup:
            errors.append("owner_release payload changed in receipt")
        per_key = actual_cleanup.get("per_key_release_measurements", []) if type(actual_cleanup) is dict else []
        expected_per_key = expected_cleanup.get("per_key_release_measurements", [])
        if per_key != expected_per_key or len(per_key) != 2:
            errors.append("per-key cleanup measurements were not preserved exactly")
        if any(row.get("actuation_id") is None or
               row.get("classification") != "CONFIRMED_PHYSICAL_UP" or
               row.get("bracket", {}).get("physical_up_interval") is None
               for row in per_key):
            errors.append("per-key receipt evidence incomplete")
    if receipt.get("current_input_authority") is not False:
        errors.append("receipt grants input authority")
    if result.get("input_sha256") != hashlib.sha256(INPUT.read_bytes()).hexdigest():
        errors.append("input hash mismatch")
    if result.get("receipt_sha256") != hashlib.sha256(receipt_raw).hexdigest():
        errors.append("receipt hash mismatch")
    audit = {"run_id": freeze["run_id"],
             "disposition": "PASS_RECONSTRUCTED_SCOPED" if not errors else "FAIL_MISMATCH",
             "early_release_count": len(receipt.get("early_releases", [])),
             "per_key_release_count": sum(len(e.get("owner_release", {}).get("per_key_release_measurements", [])) for e in receipt.get("early_releases", [])),
             "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
             "errors": errors,
             "scope": "independent receipt/raw equality audit of source-extracted guard method"}
    (OUT / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
