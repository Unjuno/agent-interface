"""Finite candidate selector; reads the declared graph only, never oracle.json."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _paths(case):
    adjacency = {}
    for source, target in case["edges"]:
        adjacency.setdefault(source, []).append(target)
    nodes = case["nodes"]
    found = []

    def visit(node, chain):
        if node in chain:
            raise ValueError("cycle requires an explicit bounded unrolling")
        path = chain + [node]
        kind = nodes.get(node, {}).get("kind")
        if kind in {"claim", "yield"}:
            found.append(path)
            return
        successors = adjacency.get(node, [])
        if not successors:
            found.append(path)
            return
        for successor in sorted(successors):
            visit(successor, path)

    visit(case["entry"], [])
    return sorted(found, key=lambda path: tuple(path))


def _claim_paths(case, paths):
    return [path for path in paths if case["nodes"].get(path[-1], {}).get("kind") == "claim"]


def _eligible(check, path, case):
    positions = {node: index for index, node in enumerate(path)}
    check_node = check["node"]
    if check_node not in positions:
        return False
    claim = case["nodes"].get(path[-1], {})
    if claim.get("obligation_from_last_effect") is True:
        effect_nodes = [node for node in path if case["nodes"].get(node, {}).get("kind") == "effect"]
        expected = case["nodes"][effect_nodes[-1]]["obligation"] if effect_nodes else None
    else:
        expected = claim.get("obligation")
    effect_positions = [i for i, node in enumerate(path) if case["nodes"].get(node, {}).get("kind") == "effect"]
    if not effect_positions or positions[check_node] <= max(effect_positions):
        return False
    generation = claim.get("generation")
    return (check.get("semantic") is True
            and expected in check.get("covers", [])
            and check.get("fresh") is True
            and check.get("generation") == generation
            and check.get("expires_generation", -1) >= generation)


def _structural_cut(check, path, case):
    positions = {node: index for index, node in enumerate(path)}
    if check["node"] not in positions:
        return False
    effect_positions = [i for i, node in enumerate(path) if case["nodes"].get(node, {}).get("kind") == "effect"]
    return bool(effect_positions) and positions[check["node"]] > max(effect_positions) and positions[check["node"]] < len(path) - 1


def _subsets(checks):
    ordered = sorted(checks, key=lambda item: item["check_id"])
    for size in range(len(ordered) + 1):
        yield from itertools.combinations(ordered, size)


def _all_paths_covered(chosen, claim_paths, case, predicate):
    return all(any(predicate(check, path, case) for check in chosen) for path in claim_paths)


def _plan(case, paths):
    claims = _claim_paths(case, paths)
    checks = case["checks"]
    if not case["graph_closed"]:
        typed = {"status": "HOLD_GRAPH_INCOMPLETE", "selected_checks": [], "total_cost": None}
    elif not claims:
        typed = {"status": "NO_SOUND_SHARED_CHECK", "selected_checks": [], "total_cost": None}
    else:
        candidates = []
        for chosen in _subsets(checks):
            if not _all_paths_covered(chosen, claims, case, _eligible):
                continue
            is_local = all(check["route_local"] for check in chosen)
            total = sum(check["cost"] for check in chosen)
            if not is_local:
                total += case["graph_maintenance_cost"]
            candidates.append((total, not is_local, len(chosen), tuple(c["check_id"] for c in chosen), chosen))

        route_local_total = 0.0
        route_local_ok = True
        for path in claims:
            choices = [c for c in checks if c["route_local"] and _eligible(c, path, case)]
            if not choices:
                route_local_ok = False
                break
            route_local_total += min(c["cost"] for c in choices)

        if not candidates:
            typed = {"status": "NO_SOUND_SHARED_CHECK", "selected_checks": [], "total_cost": None}
        else:
            best = min(candidates, key=lambda row: row[:4])
            chosen = best[4]
            selected_ids = sorted(c["check_id"] for c in chosen)
            if route_local_ok and best[0] >= route_local_total:
                selected_ids = sorted({
                    min((c for c in checks if c["route_local"] and _eligible(c, path, case)), key=lambda c: (c["cost"], c["check_id"]))["check_id"]
                    for path in claims
                })
                status = "ROUTE_LOCAL_NO_GAIN"
                total_cost = route_local_total
            else:
                status = "SHARED_CHECK_PLACED" if not all(c["route_local"] for c in chosen) else "ROUTE_LOCAL_NO_GAIN"
                total_cost = best[0]
            typed = {"status": status, "selected_checks": selected_ids, "total_cost": round(total_cost, 6)}

    graph_candidates = []
    if claims:
        for chosen in _subsets(checks):
            if _all_paths_covered(chosen, claims, case, _structural_cut):
                total = sum(check["cost"] for check in chosen) + case["graph_maintenance_cost"]
                graph_candidates.append((total, len(chosen), tuple(c["check_id"] for c in chosen), chosen))
    if graph_candidates and case["graph_closed"]:
        best_graph = min(graph_candidates, key=lambda row: row[:3])
        graph_only = {"selected_checks": sorted(c["check_id"] for c in best_graph[3]),
                      "total_cost": round(best_graph[0], 6), "claim_certified": True,
                      "claim_precedes_all_checks": False}
    else:
        graph_only = {"selected_checks": [], "total_cost": None, "claim_certified": False,
                      "claim_precedes_all_checks": any(
                          not any(_structural_cut(check, path, case) for check in checks) for path in claims
                      )}

    local_total = 0.0
    local_ok = bool(claims)
    for path in claims:
        local = [check for check in checks if check["route_local"] and _eligible(check, path, case)]
        if not local:
            local_ok = False
            break
        local_total += min(check["cost"] for check in local)
    route_local = {"total_cost": round(local_total, 6) if local_ok else None,
                   "path_count": len(claims), "all_paths_covered": local_ok}

    return {"case_id": case["case_id"],
            "paths": [{"nodes": path, "terminal_kind": case["nodes"].get(path[-1], {}).get("kind", "dead_end")} for path in paths],
            "claim_path_count": len(claims),
            "yield_path_count": sum(case["nodes"].get(path[-1], {}).get("kind") == "yield" for path in paths),
            "typed": typed, "route_local": route_local, "graph_only": graph_only}


def run(fixture):
    rows = [_plan(case, _paths(case)) for case in fixture["cases"]]
    return {"schema": "claim-postdominator-raw-v1", "fixture_sha256": hashlib.sha256(
        (HERE / "fixture.json").read_bytes()).hexdigest(), "cases": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=HERE / "fixture.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture_bytes = args.fixture.read_bytes()
    fixture = json.loads(fixture_bytes)
    raw = run(fixture)
    raw["fixture_sha256"] = hashlib.sha256(fixture_bytes).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"status": "CANDIDATE_COMPLETE", "case_count": len(raw["cases"]), "output": str(args.out)}))


if __name__ == "__main__":
    main()
