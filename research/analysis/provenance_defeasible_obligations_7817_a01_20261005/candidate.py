"""Finite, advisory-only provenance-aware obligation evaluator."""
import json
from pathlib import Path


def _scope_applies(rule_scope, context_scope):
    return all(context_scope.get(k) == v for k, v in rule_scope.items())


def _condition_applies(condition, facts):
    if condition is True:
        return True
    if not isinstance(condition, dict) or set(condition) != {"fact", "equals"}:
        return False
    return facts.get(condition["fact"], object()) == condition["equals"]


def _path(edges, start, goal):
    todo = [(start, [start])]
    while todo:
        node, chain = todo.pop(0)
        if node == goal:
            return chain
        for high, low in edges:
            if high == node and low not in chain:
                todo.append((low, chain + [low]))
    return None


def _has_cycle(edges):
    graph = {}
    for high, low in edges:
        graph.setdefault(high, []).append(low)
    visiting, visited = set(), set()

    def visit(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(next_node) for next_node in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in list(graph))


def evaluate(case, source_registry, priority_issuer_allowlist):
    if not case.get("sources_complete", False):
        return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "SOURCE_COVERAGE_INCOMPLETE", "obligations": [], "proofs": [], "authority_changed": False}
    rules = case.get("rules", [])
    ids = [r.get("id") for r in rules]
    if None in ids or len(ids) != len(set(ids)):
        return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "DUPLICATE_RULE_ID_OR_VERSION", "obligations": [], "proofs": [], "authority_changed": False}
    scope, facts = case.get("scope", {}), case.get("facts", {})
    if any(not r.get("source") or r.get("source") not in source_registry or "*" in r.get("scope", {}).values() for r in rules):
        return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "MISSING_SOURCE_OR_WIDENED_SCOPE", "obligations": [], "proofs": [], "authority_changed": False}
    for rule in rules:
        if rule.get("current", True) and _scope_applies(rule.get("scope", {}), scope):
            cond = rule.get("condition")
            if cond is not True and not (isinstance(cond, dict) and set(cond) == {"fact", "equals"} and cond["fact"] in facts):
                return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "UNKNOWN_RULE_CONDITION", "obligations": [], "proofs": [], "authority_changed": False}
            if rule.get("authority") != "authenticated":
                return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "UNAUTHENTICATED_RULE", "obligations": [], "proofs": [], "authority_changed": False}
            if rule.get("kind") not in {"STRICT", "DEFEASIBLE"} or rule.get("effect") not in {"PERMIT", "DENY"}:
                return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "UNKNOWN_RULE_TYPE_OR_EFFECT", "obligations": [], "proofs": [], "authority_changed": False}
    active = [r for r in rules if r.get("current", True) and r.get("authority") == "authenticated" and _scope_applies(r.get("scope", {}), scope) and _condition_applies(r.get("condition"), facts)]
    valid_edges = []
    active_ids = {r["id"] for r in active}
    for edge in case.get("edges", []):
        if edge.get("higher") not in active_ids or edge.get("lower") not in active_ids:
            continue
        if not edge.get("authenticated") or edge.get("issuer") not in priority_issuer_allowlist or not edge.get("current") or not edge.get("source") or edge.get("source") not in source_registry or "*" in edge.get("scope", {}).values() or not _scope_applies(edge.get("scope", {}), scope):
            return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "INVALID_PRIORITY_PROVENANCE_OR_SCOPE", "obligations": [], "proofs": [], "authority_changed": False}
        valid_edges.append((edge["higher"], edge["lower"]))
    if _has_cycle(valid_edges):
        return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "PRIORITY_CYCLE", "obligations": [], "proofs": [], "authority_changed": False}
    defeated, proofs = set(), []
    for i, left in enumerate(active):
        for right in active[i + 1:]:
            if left["effect"] == right["effect"]:
                continue
            if left["kind"] == "STRICT" or right["kind"] == "STRICT":
                return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "STRICT_RULE_ATTACK", "obligations": [], "proofs": [], "authority_changed": False}
            lr = _path(valid_edges, left["id"], right["id"])
            rl = _path(valid_edges, right["id"], left["id"])
            if bool(lr) == bool(rl):
                return {"case_id": case["id"], "status": "UNKNOWN_STOP", "reason": "UNRESOLVED_OR_AMBIGUOUS_CONFLICT", "obligations": [], "proofs": [], "authority_changed": False}
            winner, loser, chain = (left, right, lr) if lr else (right, left, rl)
            defeated.add(loser["id"])
            edge_sources = []
            for high, low in zip(chain, chain[1:]):
                edge_sources.extend(e["source"] for e in case["edges"] if e.get("higher") == high and e.get("lower") == low)
            proofs.append({"winner": winner["id"], "loser": loser["id"], "priority_path": chain, "edge_sources": edge_sources})
    obligations = sorted({r["effect"] for r in active if r["id"] not in defeated})
    return {"case_id": case["id"], "status": "RESOLVED_ADVISORY", "reason": None, "obligations": obligations, "proofs": proofs, "applicable_rule_sources": sorted(r["source"] for r in active), "authority_changed": False}


def run(fixture_path, output_path):
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    cases = fixture["contexts"]
    registry = fixture["source_registry"]
    issuer_allowlist = fixture["priority_issuer_allowlist"]
    rows = [evaluate(c, registry, issuer_allowlist) for c in cases]
    mutations = []
    change = json.loads(json.dumps(cases[0])); change["rules"][0]["source"] = ""; mutations.append(("remove_source_span", change))
    change = json.loads(json.dumps(cases[0])); change["edges"][0]["issuer"] = "forged"; mutations.append(("forge_issuer", change))
    change = json.loads(json.dumps(cases[0])); change["rules"][0]["scope"]["target"] = "*"; mutations.append(("widen_scope", change))
    change = json.loads(json.dumps(cases[0])); change["edges"].append({"higher":"default","lower":"retry","issuer":"owner","authenticated":True,"current":True,"scope":change["scope"],"source":"s4"}); mutations.append(("insert_priority_cycle", change))
    change = json.loads(json.dumps(cases[7])); change["facts"]["retry_window"] = True; change["rules"][1]["kind"] = "STRICT"; change["edges"] = [{"higher":"broad","lower":"specific","issuer":"owner","authenticated":True,"current":True,"scope":change["scope"],"source":"s3"}]; mutations.append(("defeat_strict_prohibition", change))
    mutation_rows = [{"mutation": label, "result": evaluate(case, registry, issuer_allowlist)} for label, case in mutations]
    result = {"case_count": len(cases), "rows": rows, "mutation_count": len(mutation_rows), "mutations": mutation_rows}
    Path(output_path).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    import sys
    out = run(sys.argv[1], sys.argv[2])
    print(json.dumps({"case_count": out["case_count"], "output": sys.argv[2]}, sort_keys=True))
