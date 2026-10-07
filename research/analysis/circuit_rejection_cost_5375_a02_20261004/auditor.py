import copy
import json
import sys
from pathlib import Path

CAP = 19
POLICIES = ("backend", "upstream", "reserved")


def reference(spec, scenario, policy):
    offered = scenario["offered"]
    z = {k: 0 for k in ("admission", "ingress", "parse", "normal_service", "refusal", "quarantine", "safety")}
    completed = refused = deferred = dropped = 0
    if policy == "upstream":
        z["admission"] = offered * spec["upstream_admission_cost_per_offered"]
        completed = min(offered, spec["upstream_limit"])
        deferred = offered - completed
        z["normal_service"] = completed * spec["upstream_verifier_cost_per_completed"]
        z["safety"] = spec["mandatory_safety_cost"]
    else:
        z["ingress"] = offered
        z["parse"] = offered
        if scenario["id"] == "bounded":
            completed = offered
            z["normal_service"] = completed * spec["normal_service_cost_per_request"]
        else:
            unit = scenario["reject_cost"] + scenario["quarantine_cost"]
            safety_reserve = spec["mandatory_safety_cost"] if policy == "reserved" else 0
            room = max(0, spec["capacity"] - safety_reserve - z["ingress"] - z["parse"])
            refused = offered if unit == 0 else min(offered, room // unit)
            deferred = offered - refused
            z["refusal"] = refused * scenario["reject_cost"]
            z["quarantine"] = refused * scenario["quarantine_cost"]
        if sum(z.values()) + spec["mandatory_safety_cost"] <= spec["capacity"]:
            z["safety"] = spec["mandatory_safety_cost"]
    return {"scenario": scenario["id"], "policy": policy, "eligible": True,
            "offered": offered, "completed": completed, "refused": refused,
            "deferred": deferred, "dropped": dropped, "authority": 0,
            "capacity": spec["capacity"], "cost": z, "total_cost": sum(z.values())}


def expected_raw(spec):
    rows = [reference(spec, s, p) for s in spec["scenarios"] for p in POLICIES]
    fault = reference(spec, spec["scenarios"][0], "upstream")
    fault.update({"scenario": "fault_drop", "eligible": False,
                  "deferred": fault["deferred"] - 1, "dropped": 1})
    rows.append(fault)
    return {"schema": "rejection-cost-raw-a02-v1", "allocation": spec["allocation"], "rows": rows}


def integrity_errors(spec, raw):
    errors = []
    if raw != expected_raw(spec):
        errors.append("raw_reconstruction")
    for i, row in enumerate(raw.get("rows", [])):
        if sum(row.get("cost", {}).values()) != row.get("total_cost"):
            errors.append(f"row{i}_sum")
        if row.get("total_cost", CAP + 1) > CAP:
            errors.append(f"row{i}_over_capacity")
        if row.get("offered") != row.get("completed", 0) + row.get("refused", 0) + row.get("deferred", 0) + row.get("dropped", 0):
            errors.append(f"row{i}_obligation_conservation")
        if row.get("authority") != 0:
            errors.append(f"row{i}_authority")
    return errors


def mutation_rejections(spec, raw):
    results = []
    for key, mutate in (
        ("capacity_cost", lambda r: r["rows"][0].update(total_cost=0)),
        ("obligation_deferred", lambda r: r["rows"][1].update(deferred=99)),
        ("authority_admission", lambda r: r["rows"][2].update(authority=1)),
        ("scenario_identity", lambda r: r["rows"][3].update(scenario="storm")),
    ):
        changed = copy.deepcopy(raw)
        mutate(changed)
        results.append((key, bool(integrity_errors(spec, changed))))
    return results


def decide(spec, raw):
    errors = integrity_errors(spec, raw)
    by = {(x["scenario"], x["policy"]): x for x in raw["rows"]}
    checks = {
        "storm_backend_safety_starved": by[("storm", "backend")]["cost"]["safety"] == 0,
        "storm_upstream_safety_served": by[("storm", "upstream")]["cost"]["safety"] == 1,
        "storm_reserved_safety_served": by[("storm", "reserved")]["cost"]["safety"] == 1,
        "zero_rejection_backend_safety_served": by[("zero_rejection", "backend")]["cost"]["safety"] == 1,
        "bounded_safety_served_all": all(by[("bounded", p)]["cost"]["safety"] == 1 for p in POLICIES),
        "fault_drop_excluded_and_detected": by[("fault_drop", "upstream")]["eligible"] is False and by[("fault_drop", "upstream")]["dropped"] == 1,
        "authority_admissions_zero": all(x["authority"] == 0 for x in raw["rows"]),
    }
    mutations = mutation_rejections(spec, raw)
    checks["four_mutations_rejected"] = len(mutations) == 4 and all(ok for _, ok in mutations)
    outcome = "PASS_METHOD_SCOPED" if not errors and all(checks.values()) else "FAIL_OR_HOLD"
    return {"allocation": spec["allocation"], "rows": len(raw["rows"]), "errors": errors,
            "checks": checks, "mutation_rejections": mutations, "outcome": outcome}


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raw_path, audit_path = Path(sys.argv[2]), Path(sys.argv[3])
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    raw = {"schema": "rejection-cost-raw-a02-v1", "allocation": spec["allocation"], "rows": rows}
    result = decide(spec, raw)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["outcome"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
