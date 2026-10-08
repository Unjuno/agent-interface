#!/usr/bin/env python3
"""Reconstruct post-hoc Pilot-06 dx strata from immutable raw JSON."""
import argparse
import hashlib
import json
from pathlib import Path

RAW_SHA256 = "0878c39a68fe2abea218132b307ceff77df1e9a52291ba14186f2c8c423e37a7"
AUDIT_SHA256 = "8a922fce11fcbc0daa67683ddf84e21cd99344cef4598546f56dbb49c3fc458f"
BANDS = (("0.071-<0.090", 0.071, 0.090), ("0.090-<0.120", 0.090, 0.120), ("0.120-<0.149", 0.120, 0.149))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path)
    ap.add_argument("audit", type=Path)
    args = ap.parse_args()
    raw_bytes = args.raw.read_bytes()
    audit_bytes = args.audit.read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest() != RAW_SHA256:
        raise SystemExit("STOP: formal raw SHA-256 mismatch")
    if hashlib.sha256(audit_bytes).hexdigest() != AUDIT_SHA256:
        raise SystemExit("STOP: corrected audit SHA-256 mismatch")
    raw = json.loads(raw_bytes)
    audit = json.loads(audit_bytes)
    if audit.get("formal_result_sha256") != RAW_SHA256 or audit.get("errors") != []:
        raise SystemExit("STOP: corrected audit does not bind cleanly to raw")
    if len(raw.get("seeds", [])) != 3:
        raise SystemExit("STOP: expected exactly three retained seeds")
    output = []
    total = 0
    for seed in raw["seeds"]:
        counts = {name: {"n": 0, "correct": 0, "yield": 0, "wrong": 0} for name, _, _ in BANDS}
        for row in seed["near_boundary_shift"]["rows"]:
            x = row["x"]
            dx, dy, vx, vy, confidence, visible = x
            teacher = 2 if confidence < .72 or visible < .5 else (0 if abs(dx) < .06 and abs(dy) < .06 and abs(vx)+abs(vy) < .12 else 1)
            if teacher != row["y"]:
                raise SystemExit("STOP: frozen teacher reconstruction mismatch")
            if teacher != 1:
                continue
            band = next((n for n, lo, hi in BANDS if lo <= abs(dx) < hi), None)
            if band is None:
                raise SystemExit("STOP: CORRECT row outside frozen descriptive bands")
            c = counts[band]
            c["n"] += 1
            proposal = row["proposal"]
            if proposal is None:
                c["yield"] += 1
            elif proposal == "CORRECT":
                c["correct"] += 1
            else:
                c["wrong"] += 1
        if sum(v["n"] for v in counts.values()) != 1024:
            raise SystemExit("STOP: seed row coverage mismatch")
        for band, _, _ in BANDS:
            output.append({"seed": seed["seed"], "band": band, **counts[band]})
        total += 1024
    if total != 3072:
        raise SystemExit("STOP: total row count mismatch")
    print(json.dumps({"raw_sha256": RAW_SHA256, "audit_sha256": AUDIT_SHA256, "rows": total, "strata": output}, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()

