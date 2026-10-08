"""Candidate bookkeeping projection for the frozen intake stream."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


def project(stream: dict, raw_bytes: bytes) -> dict:
    rows = stream["rows"]
    intake = [r for r in rows if r["kind"] == "intake"]
    started_tests = [r for r in rows if r["kind"] == "test" and r["test_started"]]
    eligible = [r for r in started_tests if r["statistical_eligible"]]
    deterministic = [r for r in rows if r["kind"] == "deterministic"]
    screen_counts = Counter(r["screen"] for r in intake)
    return {
        "schema": "portfolio-intake-ledger-v1",
        "fixture_id": stream["fixture_id"],
        "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "intake": {
            "count": len(intake),
            "screen_counts": dict(sorted(screen_counts.items())),
            "ids": [r["id"] for r in intake],
        },
        "started_opportunities": [
            {
                "id": r["id"],
                "claim_id": r["claim_id"],
                "outcome": r["outcome"],
                "abandoned_after_interim": r["abandoned_after_interim"],
                "statistical_eligible": r["statistical_eligible"],
            }
            for r in started_tests
        ],
        "statistical_family": [
            {"id": r["id"], "claim_id": r["claim_id"], "p_value": r["p_value"]}
            for r in eligible
        ],
        "deterministic": [
            {"id": r["id"], "outcome": r["outcome"], "hard_safety": r["hard_safety"]}
            for r in deterministic
        ],
        "counts": {
            "all_rows": len(rows),
            "screened_out_not_tested": len(intake),
            "started_test_opportunities": len(started_tests),
            "statistical_family_size": len(eligible),
            "deterministic_rows": len(deterministic),
            "started_negative_abandoned": sum(
                r["outcome"] == "TEST_STARTED_FAIL" and r["abandoned_after_interim"]
                for r in started_tests
            ),
        },
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    raw = (root / "formal_input.json").read_bytes()
    stream = json.loads(raw)
    result = project(stream, raw)
    (root / "candidate_raw.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
