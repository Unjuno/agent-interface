"""T10 candidate for finite global-section admission under typed contracts."""
from itertools import product

VARIABLES = ("x", "y", "z")


def evaluate(decision_input):
    contexts = decision_input["contexts"]
    sections = []
    for bits in product((0, 1), repeat=len(VARIABLES)):
        assignment = dict(zip(VARIABLES, bits))
        if all(any(tuple(assignment[name] for name in context["vars"]) == tuple(values)
                   for values in context["tuples"]) for context in contexts):
            sections.append(assignment)
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
        contract = decision_input["contract"]
        action = decision_input["action"]
        admitted = contract == "reversible_approximate" and action in ("reversible", "compensable")
        admitted |= (contract == "explicit_allow_approximate_irreversible"
                     and action in ("reversible", "compensable", "irreversible"))
    return {"sections": sections, "section_count": len(sections), "spread": spread,
            "status": status, "admitted": admitted}
