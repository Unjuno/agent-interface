"""One-shot synthetic invocation of the unchanged MAP01 v6 boundary audit."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
AUDIT_PATH = REPO / "research/doom/audit_map01_recovery_cover_mechanism_v6.py"
ALLOC = "MAP01-RECOVERY-V6-WINDOW-INTEGRITY-1632-T1-20261002-01"
PHASE = "immediately_after_delay_before_fallback_cleanup"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.out
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    for pair in (1, 2, 3):
        for arm in ("coast_control", "bounded_recovery"):
            row = {
                "pair_index": pair,
                "arm": arm,
                "planner_window": {
                    "start_ns": 1_000_000_000,
                    "end_ns": 1_600_000_000,
                    "duration_ns": 600_000_000,
                    "end_boundary_phase": PHASE,
                },
            }
            path = root / f"pair-{pair:02d}" / arm / "arm-summary.json"
            path.parent.mkdir(parents=True, exist_ok=False)
            path.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
            rows.append(row)

    base = types.ModuleType("audit_map01_recovery_cover_mechanism_v4")
    base.ALLOCATION_ID = "synthetic-v4-fixture"
    base.audit = lambda _root: {
        "decision": "PASS_MECHANISM_ONLY",
        "valid_experiment": True,
        "promotable_mechanism_result": True,
        "hard_failures": [],
        "hold_reasons": [],
    }
    sys.modules[base.__name__] = base
    spec = importlib.util.spec_from_file_location("unchanged_v6_audit", AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen v6 audit")
    v6 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v6)
    clean = v6.audit(root)
    payload = {
        "schema": "map01-recovery-v6-window-integrity-candidate-v1",
        "allocation_id": ALLOC,
        "frozen_main": "14b81dd1f6853623a694266b98538f812847257a",
        "v6_audit_source_sha256": hashlib.sha256(AUDIT_PATH.read_bytes()).hexdigest(),
        "v6_audit_clean": clean,
        "arm_summaries": rows,
        "explicit_boundaries": {
            "synthetic_v4_stub": True,
            "no_runtime_or_formal_allocation": True,
        },
    }
    (root / "candidate.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"candidate": "completed_once", "arm_summaries": len(rows),
                      "v6_decision": clean["decision"],
                      "planner_boundary_failures": clean["planner_boundary_failures"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
