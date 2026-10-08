"""Candidate generator for Issue #5890; synthetic finite portfolio only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

SEED = 58901002
FAMILIES = 32
SCALE = 1_000_000
KINDS = ["STAT_NULL", "STAT_ALT", "METHOD_PASS", "STAT_NULL",
         "STAT_INVALID_CORRELATED", "STAT_ALT", "METHOD_FAIL", "DESCRIPTIVE",
         "HOLD", "HARD_SAFETY_FAIL", "STOP", "STAT_NULL", "STAT_ALT"]


def draw256(token: str) -> int:
    return int.from_bytes(hashlib.sha256(token.encode("ascii")).digest(), "big")


def p_value(kind: str, family: int, slot: int) -> int:
    if kind == "STAT_NULL":
        x = draw256(f"{SEED}|{family}|{slot}|null")
        return (x * SCALE) // (1 << 256) + 1
    if kind == "STAT_ALT":
        x = draw256(f"{SEED}|{family}|{slot}|alternative")
        return (x ** 5 * (SCALE - 1)) // (1 << 1280) + 1
    return None


def online_reject(p_micro: int, eligible_order: int) -> bool:
    # Exact comparison: p/1e6 <= 5/[100*i*(i+1)].
    return p_micro * 100 * eligible_order * (eligible_order + 1) <= 5 * SCALE


def build_raw() -> dict:
    rows = []
    eligible_order = 0
    first_null_by_family = {}
    for family in range(FAMILIES):
        family_id = f"F{family:02d}"
        for slot, kind in enumerate(KINDS):
            p = p_value(kind, family, slot)
            truth = True if kind == "STAT_NULL" else False if kind == "STAT_ALT" else None
            dep = f"independent-{family}-{slot}" if truth is not None else None
            safety = kind == "HARD_SAFETY_FAIL"
            method = "PASS" if kind == "METHOD_PASS" else "FAIL" if kind == "METHOD_FAIL" else None
            description = "directional-only" if kind == "DESCRIPTIVE" else None
            if kind == "STAT_NULL":
                first_null_by_family[family] = p
            elif kind == "STAT_INVALID_CORRELATED":
                p = first_null_by_family[family]
                truth = True
                dep = f"shared-null-{family}"
            elif kind == "HARD_SAFETY_FAIL":
                p = 1  # nominally significant, but ineligible and safety-blocked.
                dep = f"safety-{family}"
            eligible = kind in {"STAT_NULL", "STAT_ALT"}
            if eligible:
                eligible_order += 1
                alpha_num, alpha_den = 5, 100 * eligible_order * (eligible_order + 1)
                naive = p * 20 < SCALE
                online = online_reject(p, eligible_order)
            else:
                alpha_num = alpha_den = None
                naive = online = False
            rows.append({
                "claim_id": f"{family_id}-C{slot+1:02d}",
                "family_id": family_id,
                "portfolio_id": "portfolio-5890-r2",
                "registered_order": len(rows) + 1,
                "completion_order": family * len(KINDS) + ((slot * 5) % len(KINDS)) + 1,
                "candidate_id": "interface-candidate-r2",
                "baseline_id": "interface-baseline-v1",
                "endpoint": "synthetic-discovery-claim",
                "claim_type": kind,
                "eligible_order": eligible_order if eligible else None,
                "p_micro": p,
                "true_null": truth,
                "dependence_group": dep,
                "hard_safety_failure": safety,
                "method_result": method,
                "descriptive_summary": description,
                "alpha_num": alpha_num,
                "alpha_den": alpha_den,
                "naive_promoted": naive,
                "online_promoted": online,
            })
    return {"schema": "portfolio-multiplicity-5890-raw-v2", "allocation": "PORTFOLIO-MULTIPLICITY-5890-T0-20261001-02",
            "base_main": "3d6ffc76d535309cf3820ed33cb9327354f03648", "seed": SEED,
            "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("refuse to overwrite candidate output")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(build_raw(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"candidate_rows={FAMILIES*len(KINDS)}")


if __name__ == "__main__":
    main()

