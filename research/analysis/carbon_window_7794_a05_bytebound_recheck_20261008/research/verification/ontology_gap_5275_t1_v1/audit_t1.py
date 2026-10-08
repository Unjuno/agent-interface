"""Independent raw-only audit; intentionally does not import candidate.py."""

import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
STOP = frozenset({
    "a", "an", "and", "as", "before", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "selected", "the", "then", "to", "under",
    "while", "with",
})
WORD = re.compile(r"[a-z0-9]+")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(raw):
    errors = []
    try:
        corpus = json.loads((HERE / "corpus.json").read_text(encoding="utf-8"))
        training = corpus["training_supported_only"]
        vocab = {t for s in training for t in WORD.findall(s.lower()) if t not in STOP}
        expected = []
        for case in corpus["evaluation"]:
            tokens = [t for t in WORD.findall(case["task_summary"].lower()) if t not in STOP]
            score = sum(t not in vocab for t in tokens) / len(tokens) if tokens else 1.0
            lexical = "UNKNOWN_CHECK_REQUIRED" if score > corpus["threshold"] else "PLAN_COVERED"
            deterministic = "PLAN_COVERED" if case.get("schema_supported", True) else "UNKNOWN_CHECK_REQUIRED"
            combined = "UNKNOWN_CHECK_REQUIRED" if "UNKNOWN_CHECK_REQUIRED" in (lexical, deterministic) else "PLAN_COVERED"
            expected.append((case, score, deterministic, lexical, combined))
        if raw.get("schema") != "ontology-gap-5275-t1-raw-v1": errors.append("schema")
        if raw.get("allocation") != "ontology-gap-5275-t1-lexical-boundary-20260930-01": errors.append("allocation")
        source = raw.get("source_identity", {})
        if source.get("corpus_sha256") != sha256(HERE / "corpus.json"): errors.append("corpus_hash")
        if source.get("candidate_sha256") != sha256(HERE / "candidate.py"): errors.append("candidate_hash")
        actual_rows = raw.get("rows", [])
        if len(actual_rows) != len(expected): errors.append("row_count")
        for got, (case, score, deterministic, lexical, combined) in zip(actual_rows, expected):
            if got.get("case_id") != case["case_id"] or got.get("family") != case["family"]: errors.append("row_identity:" + case["case_id"])
            if got.get("oracle_unknown") != case["oracle_unknown"]: errors.append("oracle_label:" + case["case_id"])
            if abs(got.get("lexical_oov_fraction", -1) - score) > 1e-12: errors.append("score:" + case["case_id"])
            for key, value in (("deterministic", deterministic), ("lexical_only", lexical), ("combined", combined)):
                if got.get(key) != value: errors.append(key + ":" + case["case_id"])
        for arm in ("deterministic", "lexical_only", "combined"):
            false_pass = [case["case_id"] for case, _, _, _, _ in expected if case["oracle_unknown"] and next((r.get(arm) for r in actual_rows if r.get("case_id") == case["case_id"]), None) != "UNKNOWN_CHECK_REQUIRED"]
            false_abstain = [case["case_id"] for case, _, _, _, _ in expected if not case["oracle_unknown"] and next((r.get(arm) for r in actual_rows if r.get("case_id") == case["case_id"]), None) == "UNKNOWN_CHECK_REQUIRED"]
            got_counts = raw.get("arms", {}).get(arm, {})
            if got_counts.get("false_pass_ids") != false_pass: errors.append("false_pass_ids:" + arm)
            if got_counts.get("false_abstain_ids") != false_abstain: errors.append("false_abstain_ids:" + arm)
            if got_counts.get("false_pass_ood") != len(false_pass): errors.append("false_pass_count:" + arm)
            if got_counts.get("false_abstain_iid") != len(false_abstain): errors.append("false_abstain_count:" + arm)
        if raw.get("counts") != {"cases": 13, "oracle_unknown": 7}: errors.append("counts")
        if raw.get("side_effects") != {"dispatches": 0, "model_calls": 0, "gpu_calls": 0, "network_calls": 0, "authority_grants": 0}: errors.append("side_effects")
        expected_disposition = "PASS_SCOPED_LEXICAL_BOUNDARY" if all(raw.get("gates", {}).values()) else "FAIL_LEXICAL_BOUNDARY"
        if raw.get("disposition") != expected_disposition: errors.append("disposition")
    except Exception as exc:
        errors.append("audit_exception:" + type(exc).__name__)
    result = {"schema": "ontology-gap-5275-t1-audit-v1", "errors": errors, "integrity_pass": not errors,
              "scientific_disposition": raw.get("disposition")}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_t1.py FORMAL-01.json")
    raise SystemExit(audit(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))))
