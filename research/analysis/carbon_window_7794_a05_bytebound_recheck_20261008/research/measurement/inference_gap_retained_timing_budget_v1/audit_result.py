from __future__ import annotations

import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "RESULT.json"
SNAPSHOT = ROOT / "SOURCE_SNAPSHOT.json"
FREEZE = ROOT / "SOURCE_FREEZE.sha256"
OUT = ROOT / "AUDIT.json"

EXPECTED_CONTROLS = {
    "changed_gap": "FAIL_SOURCE_INTEGRITY",
    "changed_drain_max": "FAIL_SOURCE_INTEGRITY",
    "missing_publication_caveat": "FAIL_PUBLICATION_CAVEAT",
    "duplicate_tag": "FAIL_DUPLICATE_TAG",
    "malformed_numeric": "FAIL_SCHEMA",
}


def parse_freeze():
    out = {}
    for line in FREEZE.read_text().splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            out[name.strip()] = digest
    return out


def main():
    result = json.loads(RESULT.read_text())
    snapshot = json.loads(SNAPSHOT.read_text())
    errors = []
    if result.get("formal_invocations") != 1 or result.get("reruns") != 0:
        errors.append("invocation_count")
    if result.get("decision") != "PASS_RETAINED_INFERENCE_GAP_TIMING_SCALE_SCOPED" or result.get("pass") is not True:
        errors.append("decision")
    if result.get("candidate_oracle_mismatch") is not False:
        errors.append("candidate_oracle")

    controls = {c.get("case"): c for c in result.get("controls", [])}
    if set(controls) != set(EXPECTED_CONTROLS):
        errors.append("control_set")
    for name, expected in EXPECTED_CONTROLS.items():
        row = controls.get(name, {})
        if row.get("got") != expected or row.get("pass") is not True:
            errors.append(f"control:{name}")

    with localcontext() as ctx:
        ctx.prec = 60
        boundary = Decimal(snapshot["t1_max_useful_effect_latency_ms"]) + Decimal(snapshot["receipt_drain"]["max_ms"])
        gaps = [Decimal(row["stdin_closed_to_exit_ms"]) for row in snapshot["rows"]]
        expected_boundary = f"{boundary:.6f}"
        expected_min_ratio = f"{min(g / boundary for g in gaps):.12f}"
        expected_max_overhead = f"{max(boundary / g for g in gaps):.15f}"
        expected_min_effective = f"{min(g - boundary for g in gaps):.6f}"
    candidate = result.get("candidate", {})
    if candidate.get("boundary_allowance_ms") != expected_boundary:
        errors.append("boundary")
    if candidate.get("min_gap_to_boundary_ratio") != expected_min_ratio:
        errors.append("min_ratio")
    if candidate.get("max_overhead_fraction") != expected_max_overhead:
        errors.append("max_overhead")
    if candidate.get("min_effective_window_ms") != expected_min_effective:
        errors.append("min_effective")
    if len(snapshot.get("rows", [])) != 10 or len({r["tag"] for r in snapshot["rows"]}) != 10:
        errors.append("source_rows")
    if snapshot.get("publication_integrity", {}).get("status") != "FAIL_MISSING" or snapshot.get("publication_integrity", {}).get("raw_reconstruction_allowed") is not False:
        errors.append("publication_caveat")

    freeze = parse_freeze()
    for name, expected in freeze.items():
        p = ROOT / name
        if not p.exists():
            errors.append(f"source_missing:{name}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            errors.append(f"source_hash:{name}")

    out = {
        "pass": not errors,
        "errors": errors,
        "decision": result.get("decision") if not errors else "FAIL_TIMING_BUDGET_INTEGRITY",
        "source_files_checked": len(freeze),
        "result_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
    }
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
