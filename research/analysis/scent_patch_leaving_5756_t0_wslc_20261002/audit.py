import collections
import hashlib
import json
import sys

EXPECTED = 360
POLICIES = {"fixed_depth_2", "exhaust_branch", "patch_leave"}


def main(path):
    raw = open(path, "rb").read()
    rows = [json.loads(line) for line in raw.decode().splitlines()]
    errors = []
    keys = [(r.get("graph_id"), r.get("policy")) for r in rows]
    if len(rows) != EXPECTED or len(set(keys)) != EXPECTED:
        errors.append("row count/uniqueness")
    if {r.get("policy") for r in rows} != POLICIES:
        errors.append("policy coverage")
    if any(r.get("unsafe_transition") for r in rows):
        errors.append("unsafe edge traversed")
    if any(r.get("stratum") == "absent" and r.get("found") for r in rows):
        errors.append("absent target scored found")
    if any(r.get("found") != r.get("oracle_found") for r in rows):
        errors.append("oracle disagreement")
    if any(not isinstance(r.get("visited_commitment"), str) or len(r["visited_commitment"]) != 64 for r in rows):
        errors.append("missing trace commitment")
    # Mutations are applied in memory and each must be rejected by these
    # independent predicates, without altering retained candidate bytes.
    mutants = []
    m = [dict(r) for r in rows]; m.pop(); mutants.append(len(m) != EXPECTED)
    m = [dict(r) for r in rows]; m[0]["unsafe_transition"] = True; mutants.append(any(x["unsafe_transition"] for x in m))
    m = [dict(r) for r in rows]; absent = next(x for x in m if x["stratum"] == "absent"); absent["found"] = True; mutants.append(any(x["stratum"] == "absent" and x["found"] for x in m))
    m = [dict(r) for r in rows]; m[0]["oracle_found"] = not m[0]["oracle_found"]; mutants.append(any(x["found"] != x["oracle_found"] for x in m))
    if not all(mutants):
        errors.append("mutation control survived")
    held = [r for r in rows if r["split"] == "heldout"]
    summary = {}
    for p in sorted(POLICIES):
        group = [r for r in held if r["policy"] == p]
        successes = [r["cost"] for r in group if r["found"] and not r["unsafe_transition"]]
        summary[p] = {"n": len(group), "successes": len(successes),
                      "success_rate": len(successes) / len(group),
                      "mean_cost_success": sum(successes) / len(successes) if successes else None}
    if errors:
        status = "FAIL_METHOD"
    else:
        c = summary["patch_leave"]; a = summary["fixed_depth_2"]; b = summary["exhaust_branch"]
        status = "H_PASS_SCOPED" if c["success_rate"] >= a["success_rate"] and c["success_rate"] >= b["success_rate"] and c["mean_cost_success"] < a["mean_cost_success"] and c["mean_cost_success"] < b["mean_cost_success"] else "NO_ADVANTAGE_SCOPED"
    print(json.dumps({"audit": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
                      "hypothesis": status, "rows": len(rows), "raw_sha256": hashlib.sha256(raw).hexdigest(),
                      "errors": errors, "mutation_controls_rejected": sum(mutants), "heldout": summary}, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
