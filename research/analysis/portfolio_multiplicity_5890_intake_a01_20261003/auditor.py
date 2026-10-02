"""Independent raw-only reconstruction; imports no candidate code."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


def reconstruct(source: dict, raw: bytes) -> dict:
    # Deliberately use an explicit row walk, separate from candidate projections.
    intake_ids, starts, family, methods = [], [], [], []
    screens: dict[str, int] = {}
    for row in source["rows"]:
        kind = row.get("kind")
        if kind == "intake":
            intake_ids.append(row["id"])
            label = row["screen"]
            screens[label] = screens.get(label, 0) + 1
        elif kind == "test":
            if row.get("test_started") is True:
                starts.append({
                    "id": row["id"],
                    "claim_id": row["claim_id"],
                    "outcome": row["outcome"],
                    "abandoned_after_interim": row["abandoned_after_interim"],
                    "statistical_eligible": row["statistical_eligible"],
                })
                if row.get("statistical_eligible") is True:
                    family.append({"id": row["id"], "claim_id": row["claim_id"], "p_value": row["p_value"]})
        elif kind == "deterministic":
            methods.append({"id": row["id"], "outcome": row["outcome"], "hard_safety": row["hard_safety"]})
        else:
            raise ValueError(f"unknown row kind: {kind!r}")
    return {
        "schema": "portfolio-intake-ledger-v1",
        "fixture_id": source["fixture_id"],
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "intake": {"count": len(intake_ids), "screen_counts": dict(sorted(screens.items())), "ids": intake_ids},
        "started_opportunities": starts,
        "statistical_family": family,
        "deterministic": methods,
        "counts": {
            "all_rows": len(source["rows"]),
            "screened_out_not_tested": len(intake_ids),
            "started_test_opportunities": len(starts),
            "statistical_family_size": len(family),
            "deterministic_rows": len(methods),
            "started_negative_abandoned": sum(
                1 for r in starts if r["outcome"] == "TEST_STARTED_FAIL" and r["abandoned_after_interim"] is True
            ),
        },
    }


def corruption_controls(expected: dict) -> dict[str, bool]:
    mutations = {}
    m = copy.deepcopy(expected); m["intake"]["ids"].pop()
    mutations["omit_intake_row"] = m
    m = copy.deepcopy(expected)
    m["started_opportunities"] = [r for r in m["started_opportunities"] if r["outcome"] != "TEST_STARTED_FAIL"]
    m["counts"]["started_test_opportunities"] -= 1
    m["counts"]["started_negative_abandoned"] = 0
    mutations["reclassify_abandoned_negative_as_untested"] = m
    m = copy.deepcopy(expected); m["started_opportunities"] = [r for r in m["started_opportunities"] if r["outcome"] != "TEST_STARTED_STOP"]
    m["counts"]["started_test_opportunities"] -= 1
    mutations["omit_started_stop"] = m
    m = copy.deepcopy(expected); m["deterministic"][0]["invented_p_value"] = 0.000001
    mutations["invent_p_for_deterministic"] = m
    m = copy.deepcopy(expected); m["deterministic"] = [r for r in m["deterministic"] if r["outcome"] != "HARD_SAFETY_FAIL"]
    m["counts"]["deterministic_rows"] -= 1
    mutations["remove_hard_safety_failure"] = m
    return {name: candidate != expected for name, candidate in mutations.items()}


def main() -> None:
    root = Path(__file__).resolve().parent
    raw = (root / "formal_input.json").read_bytes()
    source = json.loads(raw)
    candidate = json.loads((root / "candidate_raw.json").read_text(encoding="utf-8"))
    expected = reconstruct(source, raw)
    controls = corruption_controls(expected)
    result = {
        "schema": "portfolio-intake-independent-audit-v1",
        "fixture_id": source["fixture_id"],
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate_sha256": hashlib.sha256((root / "candidate_raw.json").read_bytes()).hexdigest(),
        "rows_reconstructed": expected["counts"]["all_rows"],
        "exact_replay": candidate == expected,
        "reconstructed_counts": expected["counts"],
        "corruption_controls_rejected": controls,
        "corruptions_rejected": sum(controls.values()),
        "disposition": "PASS_METHOD_SCOPED" if candidate == expected and all(controls.values()) else "FAIL_AUDIT",
        "limits": ["one authored synthetic stream", "no FDR guarantee", "no GUI/model/product claim"],
    }
    (root / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exact_replay": result["exact_replay"], "corruptions_rejected": result["corruptions_rejected"], "disposition": result["disposition"]}, sort_keys=True))


if __name__ == "__main__":
    main()
