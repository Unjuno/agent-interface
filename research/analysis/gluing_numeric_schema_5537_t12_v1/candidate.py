"""T12 finite minimax candidate with explicit residual scope for incomplete input."""
from itertools import product

VARIABLES = ("x", "y", "z")
GRID = (0, 2, 4, 6, 8)


def evaluate(source):
    scored = []
    for state in product(GRID, repeat=3):
        assignment = dict(zip(VARIABLES, state))
        residuals = [abs((assignment[edge["right"]] - assignment[edge["left"]])
                         - edge["target_ticks"]) for edge in source["relations"]]
        scored.append((max(residuals, default=0), assignment, residuals))
    observed_minimax = min((row[0] for row in scored), default=0)
    witnesses = [(assignment, residuals) for score, assignment, residuals in scored
                 if score == observed_minimax]

    if not source["complete"]:
        status = "UNKNOWN"
    elif observed_minimax == 0:
        status = "GLOBAL_SECTION_CERTIFIED"
    elif observed_minimax <= source["tolerance_ticks"]:
        status = "APPROXIMATE_SECTION"
    else:
        status = "NO_GLOBAL_SECTION"

    admitted = status == "GLOBAL_SECTION_CERTIFIED"
    if status == "APPROXIMATE_SECTION":
        contract, action = source["contract"], source["action"]
        admitted = contract == "reversible_approximate" and action in ("reversible", "compensable")
        admitted |= contract == "explicit_allow_approximate_irreversible" and action in (
            "reversible", "compensable", "irreversible")

    complete = source["complete"]
    return {
        "observed_subgraph_minimax_residual_ticks": observed_minimax,
        "residual_scope": "full_cover" if complete else "observed_subgraph_only",
        "minimax_residual_ticks": observed_minimax if complete else None,
        "optimal_witnesses": ([{"assignment_ticks": assignment, "residual_ticks": residuals}
                               for assignment, residuals in witnesses] if complete else []),
        "optimal_witness_count": len(witnesses) if complete else 0,
        "status": status,
        "admitted": admitted,
    }
