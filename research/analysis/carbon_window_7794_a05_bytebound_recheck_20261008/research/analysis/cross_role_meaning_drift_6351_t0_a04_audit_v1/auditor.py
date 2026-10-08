import json
import sys


def verdict(h):
    if h["source_epoch"] != h["verify_epoch"] or h["receipt_conflict"]:
        return "CONFLICT_NOT_PASS"
    if h["verification"] == "VERIFIED" and h["children"]:
        return "VERIFIED_WITH_CHILD_OBLIGATION"
    return h["verification"] if h["verification"] != "NOT_RUN" else "NOT_VERIFIED"


def expected_projection(h):
    return {
        "planner": "DISPATCH_UNKNOWN" if h["dispatch"] == "UNKNOWN" else "DISPATCH_ACCEPTED",
        "verifier": verdict(h),
        "effect_owner": {
            "release": h["release"],
            "effect": h["effect"],
            "children": h["children"],
            "epoch_conflict": h["source_epoch"] != h["verify_epoch"] or h["receipt_conflict"],
        },
    }


def check_projection(h, row, oracle_value):
    expected = expected_projection(h)
    return row["projection"] == expected and row["typed"] == oracle_value


def audit(raw_path, candidate_path, oracle_path):
    histories = json.load(open(raw_path, encoding="utf-8"))["histories"]
    candidates = json.load(open(candidate_path, encoding="utf-8"))
    oracle = json.load(open(oracle_path, encoding="utf-8"))["expected"]
    by_id = {row["id"]: row for row in candidates}
    rows = []
    for h in histories:
        r = by_id[h["id"]]
        expected_verdict = verdict(h)
        projected = r["projection"]
        exp_proj = expected_projection(h)
        field_checks = {
            "planner_dispatch": projected["planner"] == exp_proj["planner"],
            "verifier": projected["verifier"] == exp_proj["verifier"] == oracle[h["id"]],
            "owner_release": projected["effect_owner"]["release"] == h["release"],
            "owner_effect": projected["effect_owner"]["effect"] == h["effect"],
            "owner_children": projected["effect_owner"]["children"] == h["children"],
            "owner_epoch_conflict": projected["effect_owner"]["epoch_conflict"] == (h["source_epoch"] != h["verify_epoch"] or h["receipt_conflict"]),
            "typed_baseline": r["typed"] == expected_verdict == oracle[h["id"]],
        }
        rows.append({"id": h["id"], "fields": field_checks, "all_fields_match": all(field_checks.values())})

    sample = histories[0]
    canonical = {"id": sample["id"], "typed": verdict(sample), "projection": expected_projection(sample)}
    mutants = {}
    m = json.loads(json.dumps(canonical)); m["projection"]["planner"] = "DISPATCH_UNKNOWN"
    mutants["planner_corruption_rejected"] = not check_projection(sample, m, verdict(sample))
    released = next(h for h in histories if h["id"] == "released_no_effect")
    released_row = {"typed": verdict(released), "projection": expected_projection(released)}
    m = json.loads(json.dumps(released_row)); m["projection"]["effect_owner"]["release"] = "UNKNOWN"
    mutants["release_corruption_rejected"] = not check_projection(released, m, verdict(released))
    m = json.loads(json.dumps(canonical)); m["projection"]["effect_owner"]["effect"] = "TARGET_MATCH"
    mutants["effect_corruption_rejected"] = not check_projection(sample, m, verdict(sample))
    child = next(h for h in histories if h["id"] == "child_unresolved")
    child_row = {"typed": verdict(child), "projection": expected_projection(child)}
    child_mutant = json.loads(json.dumps(child_row)); child_mutant["projection"]["effect_owner"]["children"] = []
    mutants["child_drop_rejected"] = not check_projection(child, child_mutant, oracle[child["id"]])
    conflict = next(h for h in histories if h["id"] == "contradictory_receipts")
    conflict_row = {"typed": verdict(conflict), "projection": expected_projection(conflict)}
    conflict_mutant = json.loads(json.dumps(conflict_row)); conflict_mutant["projection"]["verifier"] = "VERIFIED"
    mutants["conflict_to_pass_rejected"] = not check_projection(conflict, conflict_mutant, oracle[conflict["id"]])
    return {"audited_rows": len(rows), "rows": rows, "mutations": mutants,
            "all_rows_match": all(row["all_fields_match"] for row in rows),
            "decision": "AUDIT_VALID" if all(row["all_fields_match"] for row in rows) and all(mutants.values()) else "AUDIT_FAIL"}


if __name__ == "__main__":
    print(json.dumps(audit(*sys.argv[1:]), sort_keys=True, separators=(",", ":")))
