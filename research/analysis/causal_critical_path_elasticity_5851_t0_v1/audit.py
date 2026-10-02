#!/usr/bin/env python3
"""Independent T0 auditor: exhaustive path enumeration and corruption rejection."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures.json"
RAW = HERE / "candidate_result.json"
OUT = HERE / "audit_result.json"


def enumerate_path(case, costs):
    outgoing = {x["id"]: [] for x in case["nodes"]}
    for a, b in case["edges"]:
        if a not in outgoing or b not in outgoing:
            return None
        outgoing[a].append(b)
    roots = [x["id"] for x in case["nodes"] if not any(x["id"] == b for _, b in case["edges"])]
    all_paths = []

    def walk(node, path, cost):
        path = path + [node]
        cost += costs[node]
        if node == case["endpoint"]:
            all_paths.append((cost, path))
        else:
            for child in outgoing[node]:
                walk(child, path, cost)

    for root in roots:
        walk(root, [], 0)
    if not all_paths:
        return None
    return max(x[0] for x in all_paths)


def audit_raw(fixture, raw):
    if raw.get("schema") != "causal-critical-path-elasticity-5851-t0-candidate-v1":
        return False
    if raw.get("fixture_sha256") != hashlib.sha256(FIX.read_bytes()).hexdigest():
        return False
    rows = raw.get("rows", [])
    cases = fixture["cases"]
    if len(rows) != len(cases) or [x.get("case_id") for x in rows] != [x["case_id"] for x in cases]:
        return False
    for case, row in zip(cases, rows):
        if case["topology"] == "unknown" or not case["clock_complete"]:
            if row.get("status") != "UNKNOWN" or row.get("numeric_elasticity") is not None:
                return False
            continue
        costs = {x["id"]: x["duration_ms"] for x in case["nodes"]}
        expected = enumerate_path(case, costs)
        if expected is None or row.get("baseline_endpoint_ms") != expected:
            return False
        output_regions = row.get("regions", {})
        expected_names = sorted(set(x["region"] for x in case["nodes"]))
        if sorted(output_regions) != expected_names:
            return False
        for region in expected_names:
            changed = costs.copy()
            for node in case["nodes"]:
                if node["region"] == region:
                    changed[node["id"]] = node["duration_ms"] // 2
            oracle_delta = expected - enumerate_path(case, changed)
            record = output_regions[region]
            if case["topology"] == "branch_change" and region == case["branch_rule"]["region"]:
                rule = case["branch_rule"]
                if record.get("intervention_status") != "NONSTATIONARY_INTERVENTION":
                    return False
                if record.get("static_bound_ms") is not None or record.get("paired_endpoint_delta_ms") is not None:
                    return False
                alt = costs["model"] + rule["amount_ms"]
                if alt > rule["threshold_ms"] and rule["alternate_endpoint_ms"] <= expected:
                    return False
            elif record.get("static_bound_ms") != oracle_delta or record.get("paired_endpoint_delta_ms") != oracle_delta:
                return False
        if row.get("status") != "MEASURED":
            return False
    by_id = {row["case_id"]: row for row in rows}
    off_path = by_id["parallel_off_path_long_span"]
    if off_path.get("sum_of_spans_top") != "diagnostic_encode" or off_path.get("largest_span_top") != "diagnostic_encode":
        return False
    if off_path["regions"]["diagnostic_encode"].get("paired_endpoint_delta_ms") != 0:
        return False
    if off_path["regions"]["model"].get("paired_endpoint_delta_ms") != 150:
        return False
    near_tie = by_id["near_tie_competing_paths"]
    if near_tie.get("baseline_endpoint_ms") != 530:
        return False
    if near_tie["regions"]["capture"].get("paired_endpoint_delta_ms") != 0:
        return False
    if near_tie["regions"]["model"].get("paired_endpoint_delta_ms") != 10:
        return False
    route = by_id["branch_changing_perturbation"]
    if route.get("paired_elasticity_top") != "NONSTATIONARY_INTERVENTION":
        return False
    return True


def main():
    if OUT.exists():
        raise SystemExit("audit output already exists; refusing overwrite")
    fixture = json.loads(FIX.read_text(encoding="utf-8"))
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    mutations = {}
    for name, mutate in [
        ("endpoint", lambda x: x["rows"][0].__setitem__("baseline_endpoint_ms", 999999)),
        ("delta", lambda x: x["rows"][1]["regions"]["diagnostic_encode"].__setitem__("paired_endpoint_delta_ms", 1)),
        ("unknown_numeric", lambda x: x["rows"][5].__setitem__("status", "MEASURED")),
        ("route_claim", lambda x: x["rows"][4]["regions"]["model"].__setitem__("paired_endpoint_delta_ms", 80)),
    ]:
        changed = copy.deepcopy(raw)
        mutate(changed)
        mutations[name] = not audit_raw(fixture, changed)
    passed = audit_raw(fixture, raw) and all(mutations.values())
    result = {"schema": "causal-critical-path-elasticity-5851-t0-audit-v1",
              "status": "PASS_METHOD_SCOPED" if passed else "FAIL_METHOD_AUDIT",
              "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
              "cases": len(raw.get("rows", [])), "independent_oracle": "exhaustive_path_enumeration",
              "primary_mismatches": 0 if audit_raw(fixture, raw) else 1,
              "corruption_controls": mutations,
              "corruption_controls_rejected": sum(mutations.values()),
              "corruption_controls_total": len(mutations)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "cases": result["cases"],
                      "controls": result["corruption_controls_rejected"]}, sort_keys=True))


if __name__ == "__main__":
    main()
