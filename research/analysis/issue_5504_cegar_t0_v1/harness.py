"""Model-free counterexample-guided refinement fixture for Issue #5504."""


INITIAL_ABSTRACTION = frozenset({"target_current"})
KNOWN_CHECKS = ("authority_current", "target_current", "evidence_current", "effect_safe", "acyclic_dependencies")
OVER_SPECIFIED_CHECKS = KNOWN_CHECKS + ("redundant_receipt_attestation", "independent_review_receipt", "clock_sync_attestation")


def _candidate_acyclic(edges):
    graph = {}
    for source, target in edges:
        graph.setdefault(source, set()).add(target)
    done = set()
    active = set()

    def visit(node):
        if node in active:
            return False
        if node in done:
            return True
        active.add(node)
        for child in graph.get(node, ()):
            if not visit(child):
                return False
        active.remove(node)
        done.add(node)
        return True

    return all(visit(node) for node in graph)


def _candidate_value(case, name):
    if name == "acyclic_dependencies":
        return _candidate_acyclic(case.get("dependencies", []))
    return case.get(name)


def coarse_decide(case):
    if not case.get("well_formed", False) or case.get("oracle_confidence", "replayed") != "replayed":
        return "UNKNOWN"
    return "ADMIT" if case.get("target_current") is True else "REJECT"


def refined_decide(case, checks):
    if not case.get("well_formed", False) or case.get("oracle_confidence", "replayed") != "replayed":
        return "UNKNOWN"
    return "ADMIT" if all(_candidate_value(case, name) is True for name in checks) else "REJECT"


def classify_counterexample(case, candidate, oracle):
    if not case.get("well_formed", False) or case.get("oracle_confidence", "replayed") != "replayed":
        return {"classification": "UNRESOLVED_UNKNOWN", "refinement": None}
    if candidate != "ADMIT" or oracle != "REJECT":
        return {"classification": "NO_REFINEMENT", "refinement": None}
    omitted_false = [name for name in KNOWN_CHECKS if name not in INITIAL_ABSTRACTION and _candidate_value(case, name) is False]
    if len(omitted_false) != 1:
        return {"classification": "UNRESOLVED_UNKNOWN", "refinement": None}
    return {"classification": "SPURIOUS_ABSTRACTION", "refinement": omitted_false[0]}


def learn(training_cases, oracle_fn):
    checks = set(INITIAL_ABSTRACTION)
    lineage = []
    for case in training_cases:
        before = refined_decide(case, checks)
        expected = oracle_fn(case)
        finding = classify_counterexample(case, before, expected)
        if finding["classification"] == "SPURIOUS_ABSTRACTION":
            predicate = finding["refinement"]
            if predicate not in checks:
                checks.add(predicate)
                lineage.append({"case_id": case["case_id"], "added_check": predicate})
    return checks, lineage
