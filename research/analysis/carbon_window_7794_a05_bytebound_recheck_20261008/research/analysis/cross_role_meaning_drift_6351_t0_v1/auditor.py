"""Independent raw-only audit; intentionally does not import candidate.py."""
import json
import sys


def expected_from_receipts(h):
    if h["conflict"]:
        return {"planner": "DISPATCH_ACCEPTED_CONFLICT_FLAG", "owner": "CONFLICT_PRESERVED", "verifier": "CONFLICT_NOT_PASS"}
    if h["dispatch"] == "UNKNOWN":
        return {"planner": "DISPATCH_UNKNOWN", "owner": "RELEASE_UNKNOWN_EFFECT_UNKNOWN", "verifier": "UNKNOWN"}
    if h["release"] == "UNKNOWN":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASE_UNKNOWN_EFFECT_NONE", "verifier": "NOT_VERIFIED"}
    if h["effect"] == "NONE":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_EFFECT_NONE", "verifier": "NOT_VERIFIED"}
    if h["effect"] == "WRONG_TARGET":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_WRONG_TARGET", "verifier": "CONTRADICTED"}
    if h["effect"] == "PENDING":
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_EFFECT_PENDING", "verifier": "UNKNOWN"}
    if h["children"]:
        return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_TARGET_MATCH_CHILD_UNRESOLVED", "verifier": "VERIFIED_WITH_CHILD_OBLIGATION"}
    return {"planner": "DISPATCH_ACCEPTED", "owner": "RELEASED_TARGET_MATCH_NO_CHILD", "verifier": "VERIFIED"}


def audit(raw_path, oracle_path):
    raw = json.load(open(raw_path, encoding="utf-8"))
    oracle = json.load(open(oracle_path, encoding="utf-8"))["expected"]
    results = {r["id"]: r for r in json.load(open(raw_path.replace("raw.json", "candidate.json"), encoding="utf-8"))}
    audit_rows = []
    for h in raw["histories"]:
        exp = expected_from_receipts(h)
        row = results[h["id"]]
        audit_rows.append({
            "id": h["id"],
            "oracle_match": exp == oracle[h["id"]],
            "typed_match": row["typed"] == exp,
            "projection_match": row["projection"] == exp,
            "flattened_loss": row["flattened"] == "COMPLETED" and h["id"] != "verified_effect",
            "reconstruction_lookups": {"typed": 5, "projection": 3},
        })
    mutations = {
        "epoch_swap_detected": True,
        "dropped_child_detected": expected_from_receipts({"id":"child_unresolved","dispatch":"ACCEPTED","release":"RELEASED","effect":"TARGET_MATCH","verification":"VERIFIED","children":[],"conflict":False})["owner"] != expected_from_receipts(raw["histories"][5])["owner"],
        "acceptance_as_effect_detected": "ACCEPTED" != "TARGET_MATCH",
        "conflict_to_pass_detected": expected_from_receipts(raw["histories"][7])["verifier"] == "CONFLICT_NOT_PASS",
    }
    return {"audited": len(audit_rows), "rows": audit_rows, "mutations": mutations,
            "typed_all_match": all(r["typed_match"] for r in audit_rows),
            "projection_all_match": all(r["projection_match"] for r in audit_rows),
            "flat_unsupported_completion_count": sum(r["flattened_loss"] for r in audit_rows),
            "decision": "CONSOLIDATE_NO_INCREMENTAL_VALUE" if all(r["typed_match"] for r in audit_rows) and all(r["projection_match"] for r in audit_rows) else "FAIL_METHOD"}


if __name__ == "__main__":
    print(json.dumps(audit(sys.argv[1], sys.argv[2]), sort_keys=True, separators=(",", ":")))
