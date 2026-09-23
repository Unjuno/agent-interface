"""Resolve the first useful feedback or terminal boundary for one action."""
import copy


def first_boundary(records, action_id):
    if not isinstance(action_id, str) or not action_id:
        raise ValueError("action id required")
    for row in records:
        if row.get("id") != action_id: continue
        if row.get("event") == "observation":
            return {"schema": "first-action-boundary-v1", "status": "FEEDBACK",
                "record": copy.deepcopy(row), "program_terminal_pending": True,
                "grants_input_authority": False}
        if row.get("event") == "terminal":
            return {"schema": "first-action-boundary-v1", "status": "TERMINAL",
                "record": copy.deepcopy(row), "program_terminal_pending": False,
                "grants_input_authority": False}
    return {"schema": "first-action-boundary-v1", "status": "PENDING",
        "record": None, "program_terminal_pending": True,
        "grants_input_authority": False}
