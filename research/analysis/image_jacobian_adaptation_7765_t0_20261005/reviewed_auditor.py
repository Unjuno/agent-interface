"""Post-formal wrapper that returns HOLD for incomplete paired raw grids."""
from __future__ import annotations

import auditor as frozen_auditor


def audit_rows(rows):
    """Refuse incomplete/duplicate pair grids before indexing arm outcomes."""
    expected = {
        (condition, seed, arm)
        for condition in frozen_auditor.P["conditions"]
        for seed in range(frozen_auditor.P["paired_held_out_seeds"])
        for arm in frozen_auditor.P["arms"]
    }
    try:
        got = [(row.get("condition"), row.get("seed"), row.get("arm"))
               for row in rows]
    except (AttributeError, TypeError):
        return {"status": "HOLD_AUDIT_OR_OUTCOME",
                "errors": ["PAIR_GRID_INCOMPLETE_OR_DUPLICATE"],
                "rows": None, "pair_grid_complete": False}
    if set(got) != expected or len(got) != len(expected):
        return {"status": "HOLD_AUDIT_OR_OUTCOME",
                "errors": ["PAIR_GRID_INCOMPLETE_OR_DUPLICATE"],
                "rows": len(got), "pair_grid_complete": False}
    result = frozen_auditor.audit_rows(rows)
    result["pair_grid_complete"] = True
    return result
