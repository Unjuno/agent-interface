#!/usr/bin/env python3
"""Post-hoc diagnostic only; does not rerun candidate or alter frozen audit/raw files."""
from __future__ import annotations

import json
import math
from pathlib import Path

import auditor

ROOT = Path(__file__).parent
OUT = ROOT / "out"
TOL = 1e-15


def main() -> None:
    public = json.loads((ROOT / "public_input.json").read_text())
    oracle = json.loads((ROOT / "oracle_input.json").read_text())
    candidate = json.loads((OUT / "candidate_output.json").read_text())
    differences, normalized = [], []
    for pub, truth, got in zip(public["cohorts"], oracle["cohorts"], candidate["records"]):
        expected = auditor.reconstruct_one(pub, truth)
        for field, want in expected.items():
            value = got.get(field)
            if isinstance(want, float):
                if not isinstance(value, (int, float)) or not math.isclose(value, want, rel_tol=0, abs_tol=TOL):
                    differences.append({"cohort": pub["cohort"], "field": field, "candidate": value, "reconstructed": want})
            elif value != want:
                differences.append({"cohort": pub["cohort"], "field": field, "candidate": value, "reconstructed": want})
        normalized.append(expected)
    result = {"classification": "POSTHOC_DIAGNOSTIC_NOT_FORMAL_PASS",
              "formal_result_preserved": True, "formal_auditor_exit": 1,
              "tolerance_absolute": TOL, "cohort_count": len(normalized),
              "fields_outside_tolerance": differences[:50],
              "fields_outside_tolerance_count": len(differences)}
    if not differences and len(normalized) == auditor.M:
        metrics = auditor.summarize(public, oracle, {"schema": "unjuno.issue8049.candidate.v1", "records": normalized})
        result["reconstructed_metrics"] = metrics
    (OUT / "POSTHOC_DIAGNOSIS.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
