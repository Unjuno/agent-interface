"""Additive retained-input verifier; never import the frozen candidate or runner.

audit_payload takes a trusted reference corpus and independently acquired source
identity. CLI pins those bytes. Unit tests may supply explicitly synthetic
reference fixtures to verify that an honest scientific FAIL is evidence-valid.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

STOP = frozenset("a an and as before by for from in into is it of on or selected the then to under while with".split())
ARMS = ("deterministic", "lexical_only", "combined")
UNKNOWN = "UNKNOWN_CHECK_REQUIRED"
PASS = "PASS_HELDOUT_LEXICAL_BOUNDARY"
FAIL = "FAIL_HELDOUT_LEXICAL_BOUNDARY"
SOURCE_PINS = {
    "corpus_sha256": "2ba0673df94c14300b12df64364fe6c708cb9a8583fee82b5d6e74eea6a88704",
    "candidate_sha256": "74d9c5e75cde6a5834418c96d44f69b0055e9e77ddb3304593be9d25d4e4fe48",
}


def same(actual, expected):
    """Typed JSON equality: Boolean/integer aliases and NaN never compare equal."""
    if type(expected) is dict:
        return type(actual) is dict and actual.keys() == expected.keys() and all(same(actual[k], v) for k, v in expected.items())
    if type(expected) is list:
        return type(actual) is list and len(actual) == len(expected) and all(same(a, e) for a, e in zip(actual, expected))
    if type(expected) is float:
        return type(actual) in (int, float) and math.isfinite(actual) and abs(actual - expected) <= 1e-12
    return type(actual) is type(expected) and actual == expected


def tokens(text):
    return [word for word in re.findall("[a-z0-9]+", text.lower()) if word not in STOP]


def reconstruct(corpus):
    vocabulary = set().union(*(set(tokens(s)) for s in corpus["training_supported_only"]))
    rows = []
    for case in corpus["evaluation"]:
        words = tokens(case["task_summary"])
        score = sum(word not in vocabulary for word in words) / len(words) if words else 1.0
        lexical = UNKNOWN if score > corpus["threshold"] else "PLAN_COVERED"
        deterministic = "PLAN_COVERED" if case.get("schema_supported", True) else UNKNOWN
        rows.append({
            "case_id": case["case_id"], "family": case["family"],
            "oracle_unknown": case["oracle_unknown"],
            "lexical_oov_fraction": score, "deterministic": deterministic,
            "lexical_only": lexical, "combined": UNKNOWN if UNKNOWN in (lexical, deterministic) else "PLAN_COVERED",
        })
    return rows, vocabulary


def arm_metrics(rows, arm):
    positives = [r for r in rows if r["oracle_unknown"] is True]
    negatives = [r for r in rows if r["oracle_unknown"] is False]
    missed = [r["case_id"] for r in positives if r[arm] != UNKNOWN]
    false_abstain = [r["case_id"] for r in negatives if r[arm] == UNKNOWN]
    return {
        "ood": len(positives), "iid": len(negatives),
        "false_pass_ood": len(missed), "false_pass_ids": missed,
        "false_abstain_iid": len(false_abstain), "false_abstain_ids": false_abstain,
        "ood_recall": (len(positives) - len(missed)) / len(positives) if positives else None,
        "iid_abstention_rate": len(false_abstain) / len(negatives) if negatives else None,
    }


def family_metrics(rows, arm):
    groups = {}
    for family in sorted({r["family"] for r in rows}):
        members = [r for r in rows if r["family"] == family]
        groups[family] = {
            "cases": len(members),
            "oracle_unknown": sum(r["oracle_unknown"] is True for r in members),
            "abstained": sum(r[arm] == UNKNOWN for r in members),
            "false_pass": sum(r["oracle_unknown"] is True and r[arm] != UNKNOWN for r in members),
            "mean_oov_fraction": sum(r["lexical_oov_fraction"] for r in members) / len(members),
        }
    return groups


def derive_gates(expected_rows, actual_rows, arms):
    actual_ids = [r.get("case_id") for r in actual_rows] if type(actual_rows) is list and all(type(r) is dict for r in actual_rows) else None
    expected_ids = [r["case_id"] for r in expected_rows]
    return {
        "corpus_counts_fixed": len(expected_rows) == 16 and sum(r["oracle_unknown"] is True for r in expected_rows) == 8 and len(set(expected_ids)) == 16 and actual_ids == expected_ids,
        "combined_iid_abstention_at_most_25pct": arms["combined"]["iid_abstention_rate"] is not None and arms["combined"]["iid_abstention_rate"] <= 0.25,
        "combined_zero_ood_false_pass": arms["combined"]["false_pass_ood"] == 0,
    }


def audit_payload(raw, corpus, source_identity):
    errors, gates, expected_disposition = [], None, None
    try:
        expected_rows, vocabulary = reconstruct(corpus)
        metrics = {arm: arm_metrics(expected_rows, arm) for arm in ARMS}
        gates = derive_gates(expected_rows, raw.get("rows"), metrics)
        expected_disposition = PASS if all(gates.values()) else FAIL
        expected = {
            "schema": "ontology-gap-5275-t2-raw-v1",
            "allocation": "ontology-gap-5275-t2-heldout-20260930-01",
            "intake_main": "30d98dcf65e9d5a1772083b416b84753f28f0b4e",
            "source_identity": source_identity,
            "training": {"supported_summaries": len(corpus["training_supported_only"]), "vocabulary_size": len(vocabulary), "threshold": corpus["threshold"]},
            "counts": {"cases": len(expected_rows), "oracle_unknown": sum(r["oracle_unknown"] is True for r in expected_rows)},
            "rows": expected_rows, "arms": metrics, "family_counts": {arm: family_metrics(expected_rows, arm) for arm in ARMS}, "gates": gates,
            "disposition": expected_disposition,
            "side_effects": {"dispatches": 0, "model_calls": 0, "gpu_calls": 0, "network_calls": 0, "authority_grants": 0},
        }
        for key, value in expected.items():
            if not same(raw.get(key), value):
                errors.append(key)
    except Exception as exc:
        errors.append("audit_exception:" + type(exc).__name__)
    return {
        "schema": "ontology-gap-5275-t2-gate-audit-v2",
        "integrity_pass": not errors, "errors": errors,
        "recomputed_gates": gates,
        "recomputed_disposition": expected_disposition,
        "scientific_disposition": expected_disposition if not errors else "NOT_VALIDATED",
        "reported_disposition": raw.get("disposition") if type(raw) is dict else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    corpus_bytes = (args.source_dir / "corpus.json").read_bytes()
    candidate_bytes = (args.source_dir / "candidate.py").read_bytes()
    identity = {"corpus_sha256": hashlib.sha256(corpus_bytes).hexdigest(), "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest()}
    raw_bytes = args.raw.read_bytes()
    raw = json.loads(raw_bytes)
    result = audit_payload(raw, json.loads(corpus_bytes), identity)
    if identity != SOURCE_PINS:
        result["errors"].append("frozen_source_identity")
        result["integrity_pass"] = False
        result["scientific_disposition"] = "NOT_VALIDATED"
    result["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    result["source_identity"] = identity
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["integrity_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
