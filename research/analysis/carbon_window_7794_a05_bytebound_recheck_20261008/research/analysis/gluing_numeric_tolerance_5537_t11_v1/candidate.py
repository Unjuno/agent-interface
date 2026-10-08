"""Candidate minimax residual solver over a small numeric evidence cover."""
from itertools import product

VARIABLES = ("x", "y", "z")


def evaluate(source):
    values = (0, 2, 4, 6, 8)  # eighth-units: 0, 1/4, 1/2, 3/4, 1
    assignments = [dict(zip(VARIABLES, state)) for state in product(values, repeat=3)]
    scores = []
    for assignment in assignments:
        residuals = [abs((assignment[edge["right"]] - assignment[edge["left"]]) - edge["target_ticks"])
                     for edge in source["relations"]]
        scores.append((max(residuals, default=0), assignment, residuals))
    minimax = min((score[0] for score in scores), default=None)
    witnesses = [(assignment, residuals) for score, assignment, residuals in scores if score == minimax]
    if not source["complete"]:
        status = "UNKNOWN"
    elif minimax == 0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif minimax is not None and minimax <= source["tolerance_ticks"]:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"
    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        contract, action = source["contract"], source["action"]
        admitted = contract == "reversible_approximate" and action in ("reversible", "compensable")
        admitted |= contract == "explicit_allow_approximate_irreversible" and action in (
            "reversible", "compensable", "irreversible")
    return {"minimax_residual_ticks": minimax,
            "optimal_witnesses": [{"assignment_ticks": a, "residual_ticks": r} for a, r in witnesses],
            "optimal_witness_count": len(witnesses), "status": status, "admitted": admitted}
