"""T9 finite global-section candidate; input/output namespaces never merge."""
from itertools import product

VARIABLES = ("x", "y", "z")


def evaluate(decision_input):
    contexts = decision_input["contexts"]
    assignments = [dict(zip(VARIABLES, bits)) for bits in product((0, 1), repeat=3)]
    sections = [assignment for assignment in assignments if all(
        any(tuple(assignment[v] for v in context["vars"]) == tuple(row)
            for row in context["tuples"]) for context in contexts
    )]
    spread = max((context["spread"] for context in contexts), default=0.0)
    if not decision_input["complete"]:
        status = "UNKNOWN"
    elif not sections:
        status = "NO_GLOBAL_SECTION"
    elif spread == 0.0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif spread <= decision_input["tolerance"]:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"
    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        admitted = decision_input["action"] in ("reversible", "compensable") or (
            decision_input["action"] == "irreversible" and
            decision_input["contract"] == "explicit_allow_approximate_irreversible"
        )
    return {"sections": sections, "section_count": len(sections), "spread": spread,
            "status": status, "admitted": admitted}
