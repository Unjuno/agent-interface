"""Run the frozen, no-dispatch lexical novelty boundary experiment once."""

import hashlib
import json
import platform
from pathlib import Path
import sys

from candidate import LexicalNoveltyModel

HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def counts(rows, arm):
    false_pass = [r["case_id"] for r in rows if r["oracle_unknown"] and r[arm] != "UNKNOWN_CHECK_REQUIRED"]
    false_abstain = [r["case_id"] for r in rows if not r["oracle_unknown"] and r[arm] == "UNKNOWN_CHECK_REQUIRED"]
    unknown = sum(r["oracle_unknown"] for r in rows)
    supported = len(rows) - unknown
    return {
        "ood": unknown,
        "iid": supported,
        "false_pass_ood": len(false_pass),
        "false_pass_ids": false_pass,
        "false_abstain_iid": len(false_abstain),
        "false_abstain_ids": false_abstain,
        "ood_recall": (unknown - len(false_pass)) / unknown if unknown else None,
        "iid_abstention_rate": len(false_abstain) / supported if supported else None,
    }


def main():
    corpus_path = HERE / "corpus.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    model = LexicalNoveltyModel.fit(corpus["training_supported_only"], corpus["threshold"])
    rows = []
    for case in corpus["evaluation"]:
        lexical_score = model.score(case["task_summary"])
        lexical = model.classify(case["task_summary"])
        deterministic = "PLAN_COVERED" if case.get("schema_supported", True) else "UNKNOWN_CHECK_REQUIRED"
        combined = (
            "UNKNOWN_CHECK_REQUIRED"
            if deterministic == "UNKNOWN_CHECK_REQUIRED" or lexical == "UNKNOWN_CHECK_REQUIRED"
            else "PLAN_COVERED"
        )
        rows.append({
            "case_id": case["case_id"],
            "family": case["family"],
            "oracle_unknown": case["oracle_unknown"],
            "t0_false_pass": case.get("t0_false_pass", False),
            "lexical_oov_fraction": lexical_score,
            "deterministic": deterministic,
            "lexical_only": lexical,
            "combined": combined,
        })
    arm_results = {
        arm: counts(rows, arm)
        for arm in ("deterministic", "lexical_only", "combined")
    }
    gates = {
        "combined_zero_ood_false_pass": arm_results["combined"]["false_pass_ood"] == 0,
        "combined_zero_iid_false_abstention": arm_results["combined"]["false_abstain_iid"] == 0,
        "all_cases_accounted": len(rows) == 13 and sum(r["oracle_unknown"] for r in rows) == 7,
    }
    raw = {
        "schema": "ontology-gap-5275-t1-raw-v1",
        "allocation": "ontology-gap-5275-t1-lexical-boundary-20260930-01",
        "intake_main": "1e34cef0b9c9b729aa0fbd32785dd658a4b6c94f",
        "runtime": {"python": platform.python_version(), "platform": sys.platform, "container": False},
        "training": {"supported_summaries": len(corpus["training_supported_only"]), "vocabulary_size": len(model.vocabulary), "threshold": model.threshold},
        "source_identity": {"corpus_sha256": sha256(corpus_path), "candidate_sha256": sha256(HERE / "candidate.py")},
        "counts": {"cases": len(rows), "oracle_unknown": sum(r["oracle_unknown"] for r in rows)},
        "arms": arm_results,
        "gates": gates,
        "disposition": "PASS_SCOPED_LEXICAL_BOUNDARY" if all(gates.values()) else "FAIL_LEXICAL_BOUNDARY",
        "rows": rows,
        "side_effects": {"dispatches": 0, "model_calls": 0, "gpu_calls": 0, "network_calls": 0, "authority_grants": 0},
    }
    print(json.dumps(raw, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
