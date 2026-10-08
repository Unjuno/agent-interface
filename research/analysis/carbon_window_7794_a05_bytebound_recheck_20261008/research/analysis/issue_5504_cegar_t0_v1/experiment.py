"""Deterministic candidate builder for the frozen Issue #5504 T0 corpus."""

import hashlib
import json
from pathlib import Path

from harness import INITIAL_ABSTRACTION, KNOWN_CHECKS, OVER_SPECIFIED_CHECKS, coarse_decide, learn, refined_decide


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def frozen_cases():
    data = json.loads((Path(__file__).with_name("cases.json")).read_text(encoding="utf-8"))
    return data


def _counts(rows, arm, split):
    selected = [row for row in rows if row["split"] == split]
    eligible = [row for row in selected if row["oracle"] in ("ADMIT", "REJECT")]
    unknown = [row for row in selected if row["oracle"] == "UNKNOWN"]
    return {
        "false_admissions": sum(row[arm] == "ADMIT" and row["oracle"] == "REJECT" for row in eligible),
        "false_rejections": sum(row[arm] == "REJECT" and row["oracle"] == "ADMIT" for row in eligible),
        "unknown_preserved": sum(row[arm] == "UNKNOWN" for row in unknown),
        "unknown_total": len(unknown),
        "authority_grants": sum(bool(row["authority_granted"]) for row in selected),
    }


def build_result(cases, oracle_fn):
    training = cases["training"]
    heldout = cases["heldout"]
    learned_checks, lineage = learn(training, oracle_fn)
    rows = []
    for split, group in (("training", training), ("heldout", heldout)):
        for case in group:
            rows.append({
                "case_id": case["case_id"],
                "split": split,
                "family": case["family"],
                "oracle": oracle_fn(case),
                "coarse": coarse_decide(case),
                "cegar": refined_decide(case, learned_checks),
                "full_oracle": refined_decide(case, KNOWN_CHECKS),
                "over_specific": refined_decide(case, OVER_SPECIFIED_CHECKS),
                "authority_granted": False,
            })
    return {
        "schema": "issue5504-cegar-t0-v1",
        "corpus_sha256": hashlib.sha256(_canonical(cases).encode("utf-8")).hexdigest(),
        "initial_checks": sorted(INITIAL_ABSTRACTION),
        "learned_checks": sorted(learned_checks),
        "lineage": lineage,
        "rows": rows,
        "comparison": {
            arm: {
                "training": _counts(rows, arm, "training"),
                "heldout": _counts(rows, arm, "heldout"),
                "heldout_false_admissions": _counts(rows, arm, "heldout")["false_admissions"],
                "heldout_false_rejections": _counts(rows, arm, "heldout")["false_rejections"],
            }
            for arm in ("coarse", "cegar", "full_oracle", "over_specific")
        },
        "check_counts": {
            "initial_coarse": len(INITIAL_ABSTRACTION),
            "cegar_learned": len(learned_checks),
            "full_required_ontology": len(KNOWN_CHECKS),
            "over_specific_static": len(OVER_SPECIFIED_CHECKS),
        },
        "scope": "synthetic finite T0 only; no production verifier or runtime authority",
    }
