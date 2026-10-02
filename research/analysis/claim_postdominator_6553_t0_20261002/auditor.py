"""Independent exact audit of candidate placements and oracle-only counterexamples."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _walk(entry, links, labels):
    """Iterative path expansion, implemented separately from candidate DFS."""
    todo = [(entry, (entry,))]
    complete = []
    bound = len(labels) + len(links) + 2
    while todo:
        current, route = todo.pop()
        kind = labels.get(current, {}).get("kind")
        if kind in ("claim", "yield"):
            complete.append(list(route))
            continue
        targets = sorted(b for a, b in links if a == current)
        if not targets:
            complete.append(list(route))
            continue
        for target in reversed(targets):
            if target in route or len(route) >= bound:
                raise ValueError("cycle or unbounded route in finite fixture")
            todo.append((target, route + (target,)))
    return sorted(complete, key=lambda route: tuple(route))


def _claim_routes(case, routes):
    return [route for route in routes if case["nodes"].get(route[-1], {}).get("kind") == "claim"]


def _after_effect_before_claim(route, node, nodes):
    if node not in route:
        return False
    index = route.index(node)
    effect_indices = [i for i, item in enumerate(route) if nodes.get(item, {}).get("kind") == "effect"]
    return bool(effect_indices) and index > max(effect_indices) and index < len(route) - 1


def _receipt_is_sound(check_id, route, claim, fixture_case, oracle_case):
    spec = next((item for item in fixture_case["checks"] if item["check_id"] == check_id), None)
    truth = oracle_case["checks"].get(check_id)
    if spec is None or truth is None or not _after_effect_before_claim(route, spec["node"], oracle_case["complete_nodes"]):
        return False
    if claim.get("obligation_from_last_effect") is True:
        effects = [node for node in route if oracle_case["complete_nodes"].get(node, {}).get("kind") == "effect"]
        expected = oracle_case["complete_nodes"][effects[-1]]["obligation"] if effects else None
    else:
        expected = claim.get("obligation")
    active_generation = claim.get("generation")
    return (expected in truth.get("covers", [])
            and truth.get("truth") is True
            and truth.get("fresh") is True
            and truth.get("generation") == active_generation
            and spec.get("semantic") is True)


def _subsets(rows):
    ordered = sorted(rows, key=lambda row: row["check_id"])
    for n in range(len(ordered) + 1):
        yield from itertools.combinations(ordered, n)


def _expected_graph_only(case, claims):
    candidates = []
    for group in _subsets(case["checks"]):
        valid = True
        for route in claims:
            if not any(_after_effect_before_claim(route, item["node"], case["nodes"]) for item in group):
                valid = False
                break
        if valid:
            cost = sum(item["cost"] for item in group) + case["graph_maintenance_cost"]
            candidates.append((cost, len(group), tuple(row["check_id"] for row in group), group))
    if not candidates or not case["graph_closed"]:
        return {"selected_checks": [], "total_cost": None, "claim_certified": False,
                "claim_precedes_all_checks": any(
                    not any(_after_effect_before_claim(route, item["node"], case["nodes"]) for item in case["checks"])
                    for route in claims)}
    best = min(candidates, key=lambda row: row[:3])
    return {"selected_checks": sorted(row["check_id"] for row in best[3]),
            "total_cost": round(best[0], 6), "claim_certified": True,
            "claim_precedes_all_checks": False}


def audit(fixture, oracle, raw):
    errors = []
    if raw.get("schema") != "claim-postdominator-raw-v1":
        errors.append("raw schema mismatch")
    expected_hash = hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest()
    if raw.get("fixture_sha256") != expected_hash:
        errors.append("fixture hash mismatch")
    cases_by_id = {row["case_id"]: row for row in fixture["cases"]}
    oracle_by_id = oracle["cases"]
    raw_by_id = {row.get("case_id"): row for row in raw.get("cases", [])}
    if set(raw_by_id) != set(cases_by_id):
        errors.append("case inventory mismatch")
    dispositions = {}
    summaries = []

    for case_id, case in cases_by_id.items():
        row = raw_by_id.get(case_id)
        oracle_case = oracle_by_id.get(case_id)
        if row is None or oracle_case is None:
            continue
        try:
            fixture_routes = _walk(case["entry"], case["edges"], case["nodes"])
            actual_routes = _walk(case["entry"], oracle_case["complete_edges"], oracle_case["complete_nodes"])
        except (KeyError, ValueError) as exc:
            errors.append(f"{case_id}: invalid finite graph: {exc}")
            continue
        emitted_routes = [item.get("nodes") for item in row.get("paths", [])]
        if emitted_routes != fixture_routes:
            errors.append(f"{case_id}: paths do not match independent enumeration")
        claims = _claim_routes(case, fixture_routes)
        full_claims = _claim_routes({**case, "nodes": oracle_case["complete_nodes"]}, actual_routes)
        graph_matches = fixture_routes == actual_routes
        if not graph_matches:
            disposition = "HOLD_GRAPH_INCOMPLETE"
            if row.get("typed", {}).get("status") != "HOLD_GRAPH_INCOMPLETE":
                errors.append(f"{case_id}: incomplete graph was not held")
        else:
            selected = row.get("typed", {}).get("selected_checks", [])
            typed_ok = bool(full_claims) and all(
                any(_receipt_is_sound(check_id, route, oracle_case["complete_nodes"].get(route[-1], {}), case, oracle_case)
                    for check_id in selected)
                for route in full_claims)
            missing_effect = any(
                not any(oracle_case["complete_nodes"].get(node, {}).get("kind") == "effect"
                        and oracle_case["complete_nodes"][node].get("obligation") == (
                            oracle_case["complete_nodes"].get(route[-1], {}).get("obligation")
                            if oracle_case["complete_nodes"].get(route[-1], {}).get("obligation_from_last_effect") is not True
                            else next((oracle_case["complete_nodes"][effect_node].get("obligation") for effect_node in reversed(route)
                                       if oracle_case["complete_nodes"].get(effect_node, {}).get("kind") == "effect"), None))
                        for node in route)
                for route in full_claims)
            early = any(
                not any(_after_effect_before_claim(route, item["node"], oracle_case["complete_nodes"])
                        for item in case["checks"])
                for route in full_claims)
            stale = any(
                spec.get("semantic") is True
                and (oracle_case["complete_nodes"].get(route[-1], {}).get("obligation")
                     if oracle_case["complete_nodes"].get(route[-1], {}).get("obligation_from_last_effect") is not True
                     else next((oracle_case["complete_nodes"][effect_node].get("obligation") for effect_node in reversed(route)
                                if oracle_case["complete_nodes"].get(effect_node, {}).get("kind") == "effect"), None))
                    in oracle_case["checks"].get(spec["check_id"], {}).get("covers", [])
                and (oracle_case["checks"].get(spec["check_id"], {}).get("fresh") is not True
                     or oracle_case["checks"].get(spec["check_id"], {}).get("generation") != oracle_case["complete_nodes"].get(route[-1], {}).get("generation"))
                for route in full_claims for spec in case["checks"]
            )
            if early:
                disposition = "HOLD_EARLY_CLAIM"
            elif not typed_ok and stale:
                disposition = "UNKNOWN_STALE_CHECK"
            elif not typed_ok or missing_effect:
                disposition = "UNKNOWN_NO_SOUND_SHARED_CHECK"
            elif row.get("typed", {}).get("status") == "ROUTE_LOCAL_NO_GAIN":
                disposition = "NO_COMPRESSION_GAIN"
            else:
                saved = row.get("route_local", {}).get("total_cost")
                placed = row.get("typed", {}).get("total_cost")
                if row.get("typed", {}).get("status") != "SHARED_CHECK_PLACED" or not isinstance(saved, (float, int)) or not isinstance(placed, (float, int)) or placed >= saved:
                    disposition = "UNKNOWN_NO_SOUND_SHARED_CHECK"
                else:
                    disposition = "PASS_TYPED_SHARED"

        expected_graph = _expected_graph_only(case, claims)
        if row.get("graph_only") != expected_graph:
            errors.append(f"{case_id}: graph-only cut/cost mismatch")
        if row.get("claim_path_count") != len(claims):
            errors.append(f"{case_id}: claim-path count mismatch")
        typed = row.get("typed", {})
        check_specs = {item["check_id"]: item for item in case["checks"]}
        selected_ids = typed.get("selected_checks", [])
        if len(selected_ids) != len(set(selected_ids)) or any(item not in check_specs for item in selected_ids):
            errors.append(f"{case_id}: typed placement contains duplicate or unknown check")
        elif typed.get("total_cost") is not None:
            selected_specs = [check_specs[item] for item in selected_ids]
            expected_cost = sum(item["cost"] for item in selected_specs)
            if any(not item["route_local"] for item in selected_specs):
                expected_cost += case["graph_maintenance_cost"]
            if round(expected_cost, 6) != typed.get("total_cost"):
                errors.append(f"{case_id}: typed placement cost mismatch")
            if typed.get("status") == "SHARED_CHECK_PLACED" and all(item["route_local"] for item in selected_specs):
                errors.append(f"{case_id}: shared placement uses only route-local checks")
            if typed.get("status") == "ROUTE_LOCAL_NO_GAIN" and any(not item["route_local"] for item in selected_specs):
                errors.append(f"{case_id}: no-gain placement contains shared check")
        local = row.get("route_local", {})
        if local.get("all_paths_covered"):
            expected_local = 0.0
            for route in claims:
                eligible = [item for item in case["checks"]
                            if item["route_local"] and _receipt_is_sound(
                                item["check_id"], route,
                                oracle_case["complete_nodes"].get(route[-1], {}), case, oracle_case)]
                if not eligible:
                    errors.append(f"{case_id}: route-local baseline claims uncovered path")
                    break
                expected_local += min(item["cost"] for item in eligible)
            if round(expected_local, 6) != local.get("total_cost"):
                errors.append(f"{case_id}: route-local baseline cost mismatch")
        dispositions[case_id] = disposition
        summaries.append({"case_id": case_id, "status": disposition,
                          "reported_path_count": len(claims),
                          "oracle_path_count": len(full_claims),
                          "typed_cost": row.get("typed", {}).get("total_cost"),
                          "route_local_cost": row.get("route_local", {}).get("total_cost"),
                          "graph_only_semantically_sound": all(
                              all(_receipt_is_sound(check_id, route, oracle_case["complete_nodes"].get(route[-1], {}), case, oracle_case)
                                  for check_id in row.get("graph_only", {}).get("selected_checks", []))
                              for route in full_claims) if row.get("graph_only", {}).get("claim_certified") else False})

    expected_statuses = {
        "positive_shared": "PASS_TYPED_SHARED",
        "no_gain_loop_exit": "NO_COMPRESSION_GAIN",
        "wrong_target": "UNKNOWN_NO_SOUND_SHARED_CHECK",
        "stale_generation": "UNKNOWN_STALE_CHECK",
        "hidden_effect": "UNKNOWN_NO_SOUND_SHARED_CHECK",
        "incomplete_graph": "HOLD_GRAPH_INCOMPLETE",
        "early_claim": "HOLD_EARLY_CLAIM",
    }
    if dispositions != expected_statuses:
        errors.append("independent dispositions differ from frozen expectations")
    positive = next((item for item in summaries if item["case_id"] == "positive_shared"), {})
    if not positive or positive.get("route_local_cost") is None or positive.get("typed_cost", 0) >= positive.get("route_local_cost", 0):
        errors.append("positive fixture did not produce a lower-cost typed shared check")
    return {"schema": "claim-postdominator-audit-v1",
            "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
            "errors": errors, "cases": summaries,
            "controls_passed": len(expected_statuses), "independent_path_enumeration": True,
            "scope": "finite synthetic workflow fixture only; no GUI, application effect, runtime cost, or safety claim"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=HERE / "fixture.json")
    parser.add_argument("--oracle", type=Path, default=HERE / "oracle.json")
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    oracle = json.loads(args.oracle.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    report = audit(fixture, oracle, raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "error_count": len(report["errors"]), "output": str(args.out)}))
    return 0 if report["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
