"""Run the frozen held-out lexical boundary experiment once."""

import hashlib
import json
import platform
from pathlib import Path
import sys

from candidate import LexicalNoveltyModel

HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows, arm):
    unknown = [r for r in rows if r["oracle_unknown"]]
    supported = [r for r in rows if not r["oracle_unknown"]]
    false_pass = [r["case_id"] for r in unknown if r[arm] != "UNKNOWN_CHECK_REQUIRED"]
    false_abstain = [r["case_id"] for r in supported if r[arm] == "UNKNOWN_CHECK_REQUIRED"]
    return {
        "ood": len(unknown), "iid": len(supported),
        "false_pass_ood": len(false_pass), "false_pass_ids": false_pass,
        "ood_recall": (len(unknown) - len(false_pass)) / len(unknown),
        "false_abstain_iid": len(false_abstain), "false_abstain_ids": false_abstain,
        "iid_abstention_rate": len(false_abstain) / len(supported),
    }


def family_counts(rows, arm):
    grouped = {}
    for row in rows:
        item = grouped.setdefault(row["family"], {"cases": 0, "oracle_unknown": 0, "abstained": 0, "false_pass": 0, "mean_oov_fraction": 0.0})
        item["cases"] += 1
        item["oracle_unknown"] += int(row["oracle_unknown"])
        item["abstained"] += int(row[arm] == "UNKNOWN_CHECK_REQUIRED")
        item["false_pass"] += int(row["oracle_unknown"] and row[arm] != "UNKNOWN_CHECK_REQUIRED")
        item["mean_oov_fraction"] += row["lexical_oov_fraction"]
    for item in grouped.values():
        item["mean_oov_fraction"] /= item["cases"]
    return grouped


def main():
    corpus_path = HERE / "corpus.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    model = LexicalNoveltyModel.fit(corpus["training_supported_only"], corpus["threshold"])
    rows = []
    for case in corpus["evaluation"]:
        score = model.score(case["task_summary"])
        lexical = model.classify(case["task_summary"])
        deterministic = "PLAN_COVERED" if case.get("schema_supported", True) else "UNKNOWN_CHECK_REQUIRED"
        combined = "UNKNOWN_CHECK_REQUIRED" if "UNKNOWN_CHECK_REQUIRED" in (lexical, deterministic) else "PLAN_COVERED"
        rows.append({
            "case_id": case["case_id"], "family": case["family"],
            "oracle_unknown": case["oracle_unknown"], "lexical_oov_fraction": score,
            "deterministic": deterministic, "lexical_only": lexical, "combined": combined,
        })
    arms = {arm: summarize(rows, arm) for arm in ("deterministic", "lexical_only", "combined")}
    by_family = {arm: family_counts(rows, arm) for arm in arms}
    gates = {
        "combined_zero_ood_false_pass": arms["combined"]["false_pass_ood"] == 0,
        "combined_iid_abstention_at_most_25pct": arms["combined"]["iid_abstention_rate"] <= 0.25,
        "corpus_counts_fixed": len(rows) == 16 and sum(r["oracle_unknown"] for r in rows) == 8,
    }
    raw = {
        "schema": "ontology-gap-5275-t2-raw-v1",
        "allocation": "ontology-gap-5275-t2-heldout-20260930-01",
        "intake_main": "30d98dcf65e9d5a1772083b416b84753f28f0b4e",
        "runtime": {"python": platform.python_version(), "platform": sys.platform, "container": False},
        "training": {"supported_summaries": len(corpus["training_supported_only"]), "vocabulary_size": len(model.vocabulary), "threshold": model.threshold},
        "source_identity": {"corpus_sha256": sha256(corpus_path), "candidate_sha256": sha256(HERE / "candidate.py")},
        "counts": {"cases": len(rows), "oracle_unknown": sum(r["oracle_unknown"] for r in rows)},
        "arms": arms, "family_counts": by_family, "gates": gates,
        "disposition": "PASS_HELDOUT_LEXICAL_BOUNDARY" if all(gates.values()) else "FAIL_HELDOUT_LEXICAL_BOUNDARY",
        "rows": rows,
        "side_effects": {"dispatches": 0, "model_calls": 0, "gpu_calls": 0, "network_calls": 0, "authority_grants": 0},
    }
    print(json.dumps(raw, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
