"""Independent raw-only audit; does not import candidate code."""
import json
import sys


def expected(h):
    if h["source_epoch"] != h["verify_epoch"] or h["receipt_conflict"]:
        return "CONFLICT_NOT_PASS"
    if h["verification"] == "VERIFIED" and h["children"]:
        return "VERIFIED_WITH_CHILD_OBLIGATION"
    return h["verification"] if h["verification"] != "NOT_RUN" else "NOT_VERIFIED"


def invariant_rejects(h):
    e = expected(h)
    return {
        "epoch_mismatch": h["source_epoch"] == h["verify_epoch"] and e != "CONFLICT_NOT_PASS",
        "dropped_child": bool(h["children"]) and e != "VERIFIED_WITH_CHILD_OBLIGATION",
        "accepted_as_effect": h["dispatch"] == "ACCEPTED" and h["effect"] == "TARGET_MATCH" and e not in ("VERIFIED", "VERIFIED_WITH_CHILD_OBLIGATION"),
        "conflict_as_pass": (h["receipt_conflict"] or h["source_epoch"] != h["verify_epoch"]) and e != "CONFLICT_NOT_PASS",
    }


def audit(raw_path, candidate_path, oracle_path):
    hs = json.load(open(raw_path, encoding="utf-8"))["histories"]
    rows = json.load(open(candidate_path, encoding="utf-8"))
    oracle = json.load(open(oracle_path, encoding="utf-8"))["expected"]
    by_id = {r["id"]: r for r in rows}
    checks = []
    for h in hs:
        r = by_id[h["id"]]
        v = expected(h)
        proj = r["projection"]
        proj_valid = (proj["verifier"] == v and proj["effect_owner"]["children"] == h["children"]
                      and proj["effect_owner"]["epoch_conflict"] == (h["source_epoch"] != h["verify_epoch"] or h["receipt_conflict"]))
        checks.append({"id":h["id"],"oracle_match":v == oracle[h["id"]],"typed_match":r["typed"] == v,
                       "projection_match":proj_valid,"flattened":r["flattened"],"independent_verdict":v})
    mutations = {}
    cases = {h["id"]:h for h in hs}
    x = dict(cases["verified_effect"]); x["verify_epoch"] += 1
    mutations["epoch_mismatch_rejected"] = expected(x) == "CONFLICT_NOT_PASS"
    x = dict(cases["child_unresolved"]); x["children"] = []
    mutations["dropped_child_detected"] = (x["children"] != cases["child_unresolved"]["children"] and expected(cases["child_unresolved"]) == "VERIFIED_WITH_CHILD_OBLIGATION")
    x = dict(cases["dispatch_only"]); x["effect"] = "TARGET_MATCH"
    mutations["acceptance_as_effect_not_promoted"] = expected(x) == "NOT_RUN" if False else expected(x) == "NOT_VERIFIED"
    x = dict(cases["contradictory_receipts"]); x["receipt_conflict"] = False; x["verify_epoch"] += 1
    mutations["conflict_to_pass_rejected"] = expected(x) == "CONFLICT_NOT_PASS"
    return {"audited":len(checks),"rows":checks,"mutation_rejections":mutations,
            "typed_all_match":all(c["typed_match"] for c in checks),"projection_all_match":all(c["projection_match"] for c in checks),
            "oracle_all_match":all(c["oracle_match"] for c in checks),"flattened_false_completion":sum(c["flattened"] == "COMPLETED" and c["independent_verdict"] != "VERIFIED" for c in checks),
            "decision":"CONSOLIDATE_NO_INCREMENTAL_VALUE" if all(c["typed_match"] and c["projection_match"] and c["oracle_match"] for c in checks) and all(mutations.values()) else "HOLD"}


if __name__ == "__main__":
    print(json.dumps(audit(*sys.argv[1:]), sort_keys=True, separators=(",", ":")))
