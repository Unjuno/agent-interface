"""Concrete fixture oracle; deliberately separate from the abstract candidate."""


def _dependency_graph_is_acyclic(edges):
    parents = {}
    for source, target in edges:
        parents.setdefault(source, []).append(target)
    visiting = set()
    visited = set()

    def visit(node):
        if node in visiting:
            return False
        if node in visited:
            return True
        visiting.add(node)
        if any(not visit(child) for child in parents.get(node, ())):
            return False
        visiting.remove(node)
        visited.add(node)
        return True

    return all(visit(node) for node in tuple(parents))


def independent_oracle(case):
    if not case.get("well_formed", False):
        return "UNKNOWN"
    if case.get("oracle_confidence", "replayed") != "replayed":
        return "UNKNOWN"
    if case.get("authority_current") is not True:
        return "REJECT"
    if case.get("target_current") is not True:
        return "REJECT"
    if case.get("evidence_current") is not True:
        return "REJECT"
    if case.get("effect_safe") is not True:
        return "REJECT"
    if not _dependency_graph_is_acyclic(case.get("dependencies", [])):
        return "REJECT"
    return "ADMIT"
