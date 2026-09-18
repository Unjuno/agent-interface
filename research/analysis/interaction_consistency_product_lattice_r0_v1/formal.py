from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

from candidate import (
    Decision,
    POLICIES,
    State,
    is_unsafe,
    oracle,
    raw_readset_admits,
    raw_surface_admits,
)

FIELDS = [
    "surface_disjoint",
    "readset_complete",
    "readset_current",
    "global_conflict_free",
    "effects_commute",
    "actuator_independent",
    "simultaneous_input_requested",
]


def all_states():
    for bits in itertools.product([False, True], repeat=len(FIELDS)):
        yield State(**dict(zip(FIELDS, bits)))


def canonical_sha(obj) -> str:
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def run(out_dir: Path):
    rows = []
    counts = {
        name: {"unsafe": 0, "false_serial": 0, "missed_full": 0, "decision_counts": {d.name: 0 for d in Decision}}
        for name in POLICIES
    }
    surface_not_readset = []
    readset_not_surface = []

    for idx, state in enumerate(all_states()):
        truth = oracle(state)
        decisions = {}
        for name, fn in POLICIES.items():
            dec = fn(state)
            decisions[name] = dec.name
            counts[name]["decision_counts"][dec.name] += 1
            counts[name]["unsafe"] += int(is_unsafe(dec, truth))
            counts[name]["false_serial"] += int(dec == Decision.SERIAL and truth != Decision.SERIAL)
            counts[name]["missed_full"] += int(dec != Decision.FULL_PARALLEL and truth == Decision.FULL_PARALLEL)

        rs = raw_surface_admits(state)
        rr = raw_readset_admits(state)
        if rs and not rr:
            surface_not_readset.append(idx)
        if rr and not rs:
            readset_not_surface.append(idx)

        rows.append({
            "index": idx,
            **state.to_dict(),
            "oracle": truth.name,
            "decisions": decisions,
        })

    product_mismatch = sum(r["decisions"]["PRODUCT"] != r["oracle"] for r in rows)
    phase_overlap_shared = sum(
        r["oracle"] == "PHASE_OVERLAP" and not r["actuator_independent"] for r in rows
    )
    full_parallel_independent = sum(
        r["oracle"] == "FULL_PARALLEL" and r["actuator_independent"] for r in rows
    )

    decision = (
        product_mismatch == 0
        and bool(surface_not_readset)
        and bool(readset_not_surface)
        and counts["SURFACE_ONLY"]["unsafe"] > 0
        and counts["READSET_ONLY"]["unsafe"] > 0
        and counts["ACTUATOR_ONLY"]["unsafe"] > 0
        and counts["SAFE_SERIAL"]["unsafe"] == 0
        and counts["SAFE_SERIAL"]["false_serial"] > 0
        and phase_overlap_shared > 0
        and full_parallel_independent > 0
    )

    summary = {
        "task": "INTERACTION-CONSISTENCY-PRODUCT-LATTICE-R0-20260919-001",
        "state_count": len(rows),
        "product_oracle_mismatch": product_mismatch,
        "surface_not_readset_count": len(surface_not_readset),
        "readset_not_surface_count": len(readset_not_surface),
        "surface_not_readset_witness": rows[surface_not_readset[0]] if surface_not_readset else None,
        "readset_not_surface_witness": rows[readset_not_surface[0]] if readset_not_surface else None,
        "phase_overlap_shared_actuator_count": phase_overlap_shared,
        "full_parallel_independent_actuator_count": full_parallel_independent,
        "policy_counts": counts,
        "decision": "PASS_CONSISTENCY_PRODUCT_NOT_SCALAR_SCOPED" if decision else "HOLD_OR_FAIL",
    }
    summary["rows_sha256"] = canonical_sha(rows)
    summary["summary_core_sha256"] = canonical_sha({k: v for k, v in summary.items() if k != "summary_core_sha256"})

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ROWS.json").write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (out_dir / "RESULT.json").write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    summary = run(Path(args.out))
    print(json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if summary["decision"].startswith("PASS_") else 2)


if __name__ == "__main__":
    main()
