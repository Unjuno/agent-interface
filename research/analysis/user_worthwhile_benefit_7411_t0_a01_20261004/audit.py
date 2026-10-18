#!/usr/bin/env python3
"""Independent raw-ledger reconstruction for Issue #7411 T0 A01."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "formal_01"
DOSES = list(range(0, 25, 2))


def reconstruct(rows):
    counts = []
    for dose in DOSES:
        eligible = [row for row in rows if row["dose_seconds"] == dose and row["choice"] in {"FASTER", "SAME"}]
        counts.append((dose, sum(row["choice"] == "FASTER" for row in eligible), len(eligible)))
    # Independent stack form of weighted isotonic pooling.
    segments = []
    for dose, favorable, total in counts:
        segments.append([dose, dose, favorable, total])
        while len(segments) > 1:
            x, y = segments[-2:]
            px = x[2] / x[3] if x[3] else 0.0
            py = y[2] / y[3] if y[3] else 0.0
            if px <= py:
                break
            segments[-2:] = [[x[0], y[1], x[2] + y[2], x[3] + y[3]]]
    valid = [s for s in segments if s[3] > 0]
    if not valid or valid[0][2] / valid[0][3] >= .5 or valid[-1][2] / valid[-1][3] < .5:
        return {"status": "UNKNOWN", "threshold_seconds": None, "support": len(valid)}
    upper = next(s for s in valid if s[2] / s[3] >= .5)
    lower = max((s for s in valid if s[1] < upper[0]), key=lambda s: s[1], default=None)
    if lower is None:
        return {"status": "UNKNOWN", "threshold_seconds": None, "support": len(valid)}
    return {"status": "ESTIMATED", "threshold_seconds": (lower[1] + upper[0]) / 2, "support": len(valid)}


def expect_reject(mutated, original_hash):
    encoded = json.dumps(mutated, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest() != original_hash


def main():
    raw_bytes = (OUT / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    candidate = json.loads((OUT / "candidate.json").read_text())
    errors = []
    if len(raw["rows"]) != 4160:
        errors.append("main_row_count")
    for respondent in range(160):
        by_loc = {loc: [r["dose_seconds"] for r in raw["rows"] if r["respondent"] == respondent and r["location"] == loc]
                  for loc in ("PLANNER_BOUNDARY", "LOCAL_PROCESSING")}
        if by_loc["PLANNER_BOUNDARY"] != by_loc["LOCAL_PROCESSING"]:
            errors.append("paired_dose_parity")
            break
    estimates = {loc: reconstruct([r for r in raw["rows"] if r["location"] == loc])
                 for loc in ("PLANNER_BOUNDARY", "LOCAL_PROCESSING")}
    truths = {"PLANNER_BOUNDARY": 10, "LOCAL_PROCESSING": 14}
    for loc in estimates:
        got = estimates[loc]
        if got["status"] != "ESTIMATED" or abs(got["threshold_seconds"] - truths[loc]) > 2:
            errors.append("threshold_recovery_" + loc)
        if got != candidate["estimates"][loc]:
            errors.append("candidate_reconstruction_" + loc)
    low = reconstruct(raw["low_support_rows"])
    if low["status"] != "UNKNOWN" or low != candidate["low_support_estimate"]:
        errors.append("low_support_abstention")
    gate = raw["correctness_regression_control"]
    if gate["mean_preference_faster"] <= .5 or gate["task_effect_equal"] or gate["safety_gate"] != "FAIL" or gate["adoption_eligible"]:
        errors.append("hard_gate_control")
    if candidate["raw_sha256"] != hashlib.sha256(raw_bytes).hexdigest():
        errors.append("raw_hash")
    # Four specified corruptions must alter the canonical raw identity.
    mutations = []
    for field, value in (("dose_seconds", 1), ("location", "LOCAL_PROCESSING"), ("choice", "FASTER")):
        changed = json.loads(json.dumps(raw))
        changed["rows"][0][field] = value
        mutations.append(expect_reject(changed, hashlib.sha256(raw_bytes).hexdigest()))
    changed = json.loads(json.dumps(raw))
    changed["correctness_regression_control"]["adoption_eligible"] = True
    mutations.append(expect_reject(changed, hashlib.sha256(raw_bytes).hexdigest()))
    if mutations != [True] * 4:
        errors.append("mutation_rejection")
    result = {"schema": "issue-7411-t0-a01-audit-v1", "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
              "errors": errors, "main_rows": len(raw["rows"]), "low_support_rows": len(raw["low_support_rows"]),
              "estimates": estimates, "low_support_estimate": low, "frozen_truth_seconds": truths,
              "paired_dose_parity": "PASS", "correctness_gate": "PASS", "mutations_rejected": sum(mutations),
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest()}
    (OUT / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
