"""Recompute the retained Docker/Xvfb direct-vs-compiled comparison."""

from __future__ import annotations

import json
import hashlib
import statistics
from pathlib import Path


ROOT = Path(__file__).parent / "docker_vizdoom_x11_caller_efficiency_20261028"
EXPECTED_PAIRS = {1, 2, 5, 6, 9, 10}
EXPECTED_GATES = {
    "route_completed": True,
    "w_observed_down": True,
    "release_verified": True,
    "independent_w_neutral": True,
    "position_changed": True,
    "effect_receipt_succeeded": True,
}


def main() -> int:
    rows: dict[tuple[int, str], dict] = {}
    for result_path in sorted(ROOT.glob("r*/arms/pair*-*/result.json")):
        record = json.loads(result_path.read_text(encoding="utf-8"))
        key = (record["pair"], record["arm"])
        if key in rows:
            raise SystemExit(f"duplicate arm: {key}")
        rows[key] = record

    expected = {(pair, arm) for pair in EXPECTED_PAIRS for arm in ("direct", "compiled")}
    if set(rows) != expected:
        raise SystemExit(f"arm set mismatch: missing={expected-set(rows)}, extra={set(rows)-expected}")

    failed_attempts = []
    custody_gaps = []
    for run_name in ("r10", "r11", "r12", "r13", "r14"):
        run_root = ROOT / run_name
        for manifest_name in ("PRETRIAL_SHA256SUMS", "POSTTRIAL_SHA256SUMS"):
            manifest_path = run_root / manifest_name
            if not manifest_path.is_file():
                custody_gaps.append({"run": run_name, "manifest": manifest_name,
                                     "status": "manifest_missing"})
                continue
            for line in manifest_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                digest, rel = line.split("  ", 1)
                path = run_root / rel
                if not path.is_file():
                    custody_gaps.append({"run": run_name, "manifest": manifest_name,
                                         "path": rel, "expected_sha256": digest,
                                         "status": "missing"})
                elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    custody_gaps.append({"run": run_name, "manifest": manifest_name,
                                         "path": rel, "expected_sha256": digest,
                                         "status": "hash_mismatch"})
    for run_name in ("r11", "r13"):
        run_root = ROOT / run_name
        conditions = json.loads((run_root / "conditions.json").read_text(encoding="utf-8"))
        matrix = json.loads((run_root / "ARM_EXIT_MATRIX.json").read_text(encoding="utf-8"))
        if len(matrix) != 4 or conditions.get("no_retries") is not True:
            raise SystemExit(f"failed-attempt ledger malformed: {run_name}")
        condition_arms = {
            (block["pair"], arm)
            for block in conditions["arms"]
            for arm in block["order"]
        }
        matrix_arms = {(row["pair"], row["arm"]) for row in matrix}
        if condition_arms != matrix_arms:
            raise SystemExit(f"failed-attempt matrix mismatch: {run_name}")
        if any(row.get("result") != "missing" or row.get("docker_exit") not in (1, 2)
               for row in matrix):
            raise SystemExit(f"failed-attempt disposition changed: {run_name}")
        failed_attempts.extend({"run": run_name, **row} for row in matrix)

    for key, record in rows.items():
        if not record.get("passed") or record.get("outcome") != "PASS_SCOPED_ARM":
            raise SystemExit(f"arm did not pass: {key}")
        gates = record.get("gates", {})
        if any(gates.get(gate) is not expected for gate, expected in EXPECTED_GATES.items()):
            raise SystemExit(f"gate mismatch: {key}")
        if not record.get("no_model_provider_calls"):
            raise SystemExit(f"unexpected model/provider use: {key}")

    direct = [rows[(pair, "direct")]["dispatch_elapsed_ms"] for pair in sorted(EXPECTED_PAIRS)]
    compiled = [rows[(pair, "compiled")]["dispatch_elapsed_ms"] for pair in sorted(EXPECTED_PAIRS)]
    differences = [c - d for c, d in zip(compiled, direct, strict=True)]
    relative = [(c / d - 1) * 100 for c, d in zip(compiled, direct, strict=True)]
    summary = {
        "status": "PASS_METRICS_WITH_CUSTODY_GAPS" if custody_gaps
                  else "PASS_COMPLETE_ATTEMPT_AUDIT",
        "arm_count": len(rows),
        "all_attempt_denominator": len(rows) + len(failed_attempts),
        "completed_passing_arms": len(rows),
        "preinput_failed_arms": len(failed_attempts),
        "failed_attempt_pairs": sorted({row["pair"] for row in failed_attempts}),
        "failed_attempt_matrix": failed_attempts,
        "posttrial_custody_gap_count": len(custody_gaps),
        "posttrial_custody_gaps": custody_gaps,
        "all_attempt_evidence_complete": not custody_gaps,
        "pair_ids": sorted(EXPECTED_PAIRS),
        "arm_types": ["direct", "compiled"],
        "all_scoped_gates_passed": True,
        "no_model_provider_calls": True,
        "direct_median_ms": statistics.median(direct),
        "compiled_median_ms": statistics.median(compiled),
        "compiled_minus_direct_pair_median_ms": statistics.median(differences),
        "compiled_minus_direct_pair_mean_ms": statistics.mean(differences),
        "compiled_relative_pair_median_percent": statistics.median(relative),
        "compiled_slower_pairs": sum(delta > 0 for delta in differences),
        "scope": "local Docker Desktop Linux Engine/Xvfb ViZDoom MAP01 one-action effect/release path; descriptive only",
        "excludes": [
            "Win32 exception/expiry recovery",
            "model/provider and token accounting",
            "startup and alias mint/preflight",
            "MAP01 completion and broad reliability",
        ],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
