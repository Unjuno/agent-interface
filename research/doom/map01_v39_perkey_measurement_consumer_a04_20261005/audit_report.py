"""Read-only independent reconstruction and provenance audit for A04."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import audit

HERE = Path(__file__).resolve().parent
A03 = HERE.parent / "map01_v39_perkey_measurement_consumer_a03_20261005"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_report() -> dict:
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    errors = []
    for relative, expected in freeze["source_sha256"].items():
        if digest(HERE / relative) != expected:
            errors.append("A04 source hash mismatch: " + relative)
    for name, identity in freeze["a03"]["files"].items():
        if digest(A03 / name) != identity["sha256"]:
            errors.append("A03 source/raw changed: " + name)
    raw_path = A03 / "INPUT_EVENTS.jsonl"
    if digest(raw_path) != freeze["input"]["sha256"]:
        errors.append("retained input hash mismatch")
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()
            if line]
    reconstructed = audit.independently_reconstruct(rows)
    expected = {"down": [87811364890958, 87811364895916],
                "up": [87811364946333, 87811364949416]}
    if reconstructed != expected:
        errors.append("independent intervals differ from retained exact baseline")
    return {
        "schema": "map01_v39_perkey_measurement_consumer_a04_audit_v1",
        "run_id": freeze["run_id"],
        "disposition": "PASS_EXACT_OWNER_INTERVAL_BOUNDARY" if not errors else "FAIL_INTEGRITY",
        "raw_input_sha256": digest(raw_path),
        "a03_frozen_inputs_unchanged": not any(
            error.startswith("A03 source/raw changed") or error == "retained input hash mismatch"
            for error in errors),
        "independent_reconstruction": reconstructed,
        "error_count": len(errors),
        "errors": errors,
        "scope": "offline exact-type boundary only; retained fake-display pair",
    }


def main() -> None:
    report = build_report()
    destination = HERE / "results" / "a04" / "AUDIT.json"
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
