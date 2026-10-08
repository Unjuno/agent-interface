import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent
EXPECTED = {
    "audit.py": "2f332c7a1f415d1990e76d00143ff15edf17ee9f4440e2afcaba767099041083",
    "trace.json": "5a60df268a80551f860d2b7859356f677ea01278b27d41ed2ef82036ddb8bc97",
    "raw.jsonl": "af9dace34a667a2e75c002c0848286801237de52e2c27b3f698fabb5010b565f",
}


def sha256_payload(path):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest == EXPECTED[path.name]:
        return digest, "exact"
    if data.endswith(b"\n"):
        digest_without_final_lf = hashlib.sha256(data[:-1]).hexdigest()
        if digest_without_final_lf == EXPECTED[path.name]:
            return digest_without_final_lf, "exact_after_single_transport_LF"
    raise ValueError("source_hash_mismatch:" + path.name)


trace_path = DATA / "trace.json"
raw_path = DATA / "raw.jsonl"
sha = {name: sha256_payload(DATA / name) for name in EXPECTED}
trace = json.loads(trace_path.read_text(encoding="utf-8"))
rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
policies = trace["policies"]
predicates = trace["predicates"]
states = trace["states"]
expected_keys = {(p, s["id"], q) for p in policies for s in states for q in predicates}
keys = [(r.get("policy"), r.get("state"), r.get("predicate")) for r in rows]
errors = []
if len(rows) != len(expected_keys) or set(keys) != expected_keys or len(set(keys)) != len(keys):
    errors.append("identity_or_denominator")
state_by_id = {state["id"]: state for state in states}


def oracle(state, predicate):
    context = state["context"]
    if predicate == "READY_TO_SUBMIT":
        if context["form"]["mode"] != "submit":
            return "DEFER"
        return "ALLOW" if context["risk"]["level"] == "safe" else "YIELD"
    if predicate == "TARGET_MATCH":
        return context["target"]["id"] == context["intent"]["target_id"]
    raise ValueError("unknown_predicate:" + predicate)


recomputed = []
for row in rows:
    expected = oracle(state_by_id[row["state"]], row["predicate"])
    if row.get("oracle_value") != expected:
        errors.append("oracle_value_mismatch:" + ":".join(keys[rows.index(row)]))
    if row.get("action") in ("MISS", "RECOMPUTE"):
        recomputed.append(row)
        if row.get("value") != expected:
            errors.append("recomputed_value_mismatch:" + ":".join((row["policy"], row["state"], row["predicate"])))
audit_result = json.loads((ROOT / "audit.json").read_text(encoding="utf-8"))
if audit_result.get("result") != "PASS_DYNAMIC_READSET_SCOPED" or audit_result.get("errors") != []:
    errors.append("corrected_audit_result")
if audit_result.get("metrics", {}).get("rows") != 64:
    errors.append("audit_row_count")
if audit_result.get("metrics", {}).get("mutation_controls_rejected") != 10:
    errors.append("audit_mutation_control_count")
stale_negative = [r for r in rows if r["policy"] == "STATIC_DECLARED" and r["action"] == "HIT" and r["value"] != oracle(state_by_id[r["state"]], r["predicate"]) and r.get("unsafe_reuse") is True]
if len(stale_negative) != 1:
    errors.append("static_declared_negative_control")
result = {
    "result": "PASS_INDEPENDENT_RECOMPUTE_VALUE_AUDIT" if not errors else "FAIL_INDEPENDENT_RECOMPUTE_VALUE_AUDIT",
    "errors": errors,
    "rows": len(rows),
    "recomputed_rows_checked": len(recomputed),
    "static_declared_stale_hit_preserved": len(stale_negative),
    "source_sha256": sha,
    "candidate_audit_controls_rejected": audit_result.get("metrics", {}).get("mutation_controls_rejected"),
}
print(json.dumps(result, indent=2, sort_keys=True))
if errors:
    raise SystemExit(1)
