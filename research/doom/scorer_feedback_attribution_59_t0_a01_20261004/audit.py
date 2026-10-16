"""Independent result audit; does not execute the candidate attribution code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPECTED = {
    "one_intent_full_coverage": "TEMPORALLY_UNIQUE",
    "one_intent_partial_coverage": "UNRESOLVED",
    "two_intents_overlap": "AMBIGUOUS",
    "missing_coverage": "UNRESOLVED",
    "unverified_other_intent_may_persist": "AMBIGUOUS",
    "same_intent_gap": "UNRESOLVED",
}


def audit():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    for relative, expected in freeze["sources"].items():
        actual = hashlib.sha256((HERE / relative).read_bytes()).hexdigest()
        assert actual == expected, (relative, actual)
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    assert result["status"] == "PASS_SCOPED"
    assert result["causation_claim"] == "NOT_ESTABLISHED"
    assert result["case_count"] == len(EXPECTED)
    assert set(row["case"] for row in result["cases"]) == set(EXPECTED)
    for row in result["cases"]:
        expected = EXPECTED[row["case"]]
        observed = row["observed"]
        assert row["expected"] == expected
        assert observed["status"] == expected
        assert observed["causal_attribution"] == "NOT_ESTABLISHED"
        if expected != "TEMPORALLY_UNIQUE":
            assert observed["intent_token"] is None
    return {
        "schema": "scorer-feedback-attribution-audit-v1",
        "status": "PASS_SCOPED",
        "independent_checks": ["frozen source hashes", "six expected case dispositions", "no causal attribution promotion", "no intent on unresolved or ambiguous cases"],
        "case_count": len(EXPECTED),
        "scope": "audit validates retained synthetic construction result only",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
