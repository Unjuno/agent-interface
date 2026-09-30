"""Independent raw-only auditor; does not import candidate.py or run_t2.py."""

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
        vocab = {token for summary in corpus["training_supported_only"] for token in WORD.findall(summary.lower()) if token not in STOP}
        expected = []
        for case in corpus["evaluation"]:
            tokens = [token for token in WORD.findall(case["task_summary"].lower()) if token not in STOP]
            score = sum(token not in vocab for token in tokens) / len(tokens) if tokens else 1.0
            lexical = "UNKNOWN_CHECK_REQUIRED" if score > corpus["threshold"] else "PLAN_COVERED"
            deterministic = "PLAN_COVERED" if case.get("schema_supported", True) else "UNKNOWN_CHECK_REQUIRED"
            combined = "UNKNOWN_CHECK_REQUIRED" if "UNKNOWN_CHECK_REQUIRED" in (lexical, deterministic) else "PLAN_COVERED"
            expected.append((case, score, deterministic, lexical, combined))
        if raw.get("schema") != "ontology-gap-5275-t2-raw-v1": errors.append("schema")
        if raw.get("allocation") != "ontology-gap-5275-t2-heldout-20260930-01": errors.append("allocation")
        source = raw.get("source_identity", {})
        if source.get("corpus_sha256") != sha256(HERE / "corpus.json"): errors.append("corpus_hash")
        if source.get("candidate_sha256") != sha256(HERE / "candidate.py"): errors.append("candidate_hash")
        actual = raw.get("rows", [])
        if len(actual) != len(expected): errors.append("row_count")
        for got, (case, score, deterministic, lexical, combined) in zip(actual, expected):
            if got.get("case_id") != case["case_id"] or got.get("family") != case["family"]: errors.append("row_identity:" + case["case_id"])
            if got.get("oracle_unknown") != case["oracle_unknown"]: errors.append("oracle_label:" + case["case_id"])
            if abs(got.get("lexical_oov_fraction", -1) - score) > 1e-12: errors.append("score:" + case["case_id"])
            for key, value in (("deterministic", deterministic), ("lexical_only", lexical), ("combined", combined)):
                if got.get(key) != value: errors.append(key + ":" + case["case_id"])
        for arm in ("deterministic", "lexical_only", "combined"):
            unknown = [case for case, *_ in expected if case["oracle_unknown"]]
            supported = [case for case, *_ in expected if not case["oracle_unknown"]]
            fp = [case["case_id"] for case in unknown if next((r.get(arm) for r in actual if r.get("case_id") == case["case_id"]), None) != "UNKNOWN_CHECK_REQUIRED"]
            fa = [case["case_id"] for case in supported if next((r.get(arm) for r in actual if r.get("case_id") == case["case_id"]), None) == "UNKNOWN_CHECK_REQUIRED"]
            metrics = raw.get("arms", {}).get(arm, {})
            if metrics.get("false_pass_ids") != fp or metrics.get("false_pass_ood") != len(fp): errors.append("false_pass:" + arm)
            if metrics.get("false_abstain_ids") != fa or metrics.get("false_abstain_iid") != len(fa): errors.append("false_abstain:" + arm)
            expected_recall = (len(unknown) - len(fp)) / len(unknown)
            expected_abstention = len(fa) / len(supported)
            if abs(metrics.get("ood_recall", -1) - expected_recall) > 1e-12: errors.append("ood_recall:" + arm)
            if abs(metrics.get("iid_abstention_rate", -1) - expected_abstention) > 1e-12: errors.append("iid_rate:" + arm)
        if raw.get("counts") != {"cases": 16, "oracle_unknown": 8}: errors.append("counts")
        for arm in ("deterministic", "lexical_only", "combined"):
            expected_families = {}
            for got, (case, score, *_rest) in zip(actual, expected):
                group = expected_families.setdefault(case["family"], {"cases": 0, "oracle_unknown": 0, "abstained": 0, "false_pass": 0, "mean_oov_fraction": 0.0})
                group["cases"] += 1
                group["oracle_unknown"] += int(case["oracle_unknown"])
                group["abstained"] += int(got[arm] == "UNKNOWN_CHECK_REQUIRED")
                group["false_pass"] += int(case["oracle_unknown"] and got[arm] != "UNKNOWN_CHECK_REQUIRED")
                group["mean_oov_fraction"] += score
            for group in expected_families.values():
                group["mean_oov_fraction"] /= group["cases"]
            if raw.get("family_counts", {}).get(arm) != expected_families: errors.append("family_counts:" + arm)
        gates = raw.get("gates", {})
        if gates.get("combined_zero_ood_false_pass") != (raw.get("arms", {}).get("combined", {}).get("false_pass_ood") == 0): errors.append("gate_ood")
        if gates.get("combined_iid_abstention_at_most_25pct") != (raw.get("arms", {}).get("combined", {}).get("iid_abstention_rate", 1) <= 0.25): errors.append("gate_iid")
        if raw.get("side_effects") != {"dispatches": 0, "model_calls": 0, "gpu_calls": 0, "network_calls": 0, "authority_grants": 0}: errors.append("side_effects")
        expected_disposition = "PASS_HELDOUT_LEXICAL_BOUNDARY" if all(gates.values()) else "FAIL_HELDOUT_LEXICAL_BOUNDARY"
        if raw.get("disposition") != expected_disposition: errors.append("disposition")
    except Exception as exc:
        errors.append("audit_exception:" + type(exc).__name__)
    result = {"schema": "ontology-gap-5275-t2-audit-v1", "errors": errors, "integrity_pass": not errors,
              "scientific_disposition": raw.get("disposition")}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: audit_t2.py FORMAL-01.json")
    raise SystemExit(audit(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))))
