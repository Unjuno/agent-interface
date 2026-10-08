from __future__ import annotations

import copy
import json
from decimal import Decimal
from pathlib import Path

from candidate import analyze, fingerprint
from oracle import compute

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "SOURCE_SNAPSHOT.json"
FP = ROOT / "SOURCE_FINGERPRINT.txt"
RESULT = ROOT / "RESULT.json"


def control(name, snapshot, expected, expected_fp):
    got = analyze(snapshot, expected_fp)
    return {"case": name, "expected": expected, "got": got["disposition"], "pass": got["disposition"] == expected}


def main():
    snapshot = json.loads(SNAPSHOT.read_text())
    expected_fp = FP.read_text().strip()
    candidate = analyze(snapshot, expected_fp)
    oracle = compute(snapshot)
    comparable = {key: candidate[key] for key in oracle} if candidate.get("ok") else None
    mismatch = comparable != oracle

    controls = []
    changed_gap = copy.deepcopy(snapshot)
    changed_gap["rows"][0]["stdin_closed_to_exit_ms"] = "12275.2936"
    controls.append(control("changed_gap", changed_gap, "FAIL_SOURCE_INTEGRITY", expected_fp))

    changed_drain = copy.deepcopy(snapshot)
    changed_drain["receipt_drain"]["max_ms"] = "5.182662"
    controls.append(control("changed_drain_max", changed_drain, "FAIL_SOURCE_INTEGRITY", expected_fp))

    missing_caveat = copy.deepcopy(snapshot)
    missing_caveat["publication_integrity"]["raw_reconstruction_allowed"] = True
    controls.append(control("missing_publication_caveat", missing_caveat, "FAIL_PUBLICATION_CAVEAT", expected_fp))

    duplicate = copy.deepcopy(snapshot)
    duplicate["rows"][1]["tag"] = duplicate["rows"][0]["tag"]
    controls.append(control("duplicate_tag", duplicate, "FAIL_DUPLICATE_TAG", expected_fp))

    malformed = copy.deepcopy(snapshot)
    malformed["rows"][0]["stdin_closed_to_exit_ms"] = "not-a-number"
    controls.append(control("malformed_numeric", malformed, "FAIL_SCHEMA", expected_fp))

    min_ratio = Decimal(candidate.get("min_gap_to_boundary_ratio", "0")) if candidate.get("ok") else Decimal(0)
    max_overhead = Decimal(candidate.get("max_overhead_fraction", "1")) if candidate.get("ok") else Decimal(1)
    min_effective = Decimal(candidate.get("min_effective_window_ms", "0")) if candidate.get("ok") else Decimal(0)
    source_rows_ok = candidate.get("n") == 10 and all(m["tag"] in {"02","03","04","05","06","07","08","09","10","11"} for m in candidate.get("metrics", []))
    gates = {
        "candidate_ok": candidate.get("ok") is True,
        "candidate_oracle_mismatch0": not mismatch,
        "source_rows_preserved": source_rows_ok,
        "boundary_allowance_exact": candidate.get("boundary_allowance_ms") == "7.874979",
        "all_gap_ratio_ge_100": min_ratio >= Decimal("100"),
        "all_effective_positive": min_effective > 0,
        "all_overhead_lt_1pct": max_overhead < Decimal("0.01"),
        "controls_pass": all(c["pass"] for c in controls),
    }
    passed = all(gates.values())
    out = {
        "task": "INFERENCE-GAP-RETAINED-TIMING-BUDGET-20260918-001",
        "formal_invocations": 1,
        "reruns": 0,
        "source_fingerprint": expected_fp,
        "candidate": candidate,
        "oracle": oracle,
        "candidate_oracle_mismatch": mismatch,
        "controls": controls,
        "gates": gates,
        "decision": "PASS_RETAINED_INFERENCE_GAP_TIMING_SCALE_SCOPED" if passed else ("HOLD_TIMING_SCALE_TOO_TIGHT" if candidate.get("ok") and (min_ratio < 100 or max_overhead >= Decimal("0.01") or min_effective <= 0) else "FAIL_TIMING_BUDGET_INTEGRITY"),
        "pass": passed,
    }
    RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
