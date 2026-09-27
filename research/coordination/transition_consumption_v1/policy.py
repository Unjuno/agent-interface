"""Frozen policy for one-use confirmation transition experiment."""


def confirmation_identity(state):
    return (state["confirmation_content_id"], int(state["confirmation_revision"]))


def classify(state, mode):
    """Return whether the current confirmation identity may authorize one transition."""
    if mode == "reusable":
        return "AUTHORIZE_TRANSITION"
    if mode == "one_use":
        if bool(state["confirmation_consumed"]):
            return "HOLD_CONFIRMATION_CONSUMED"
        return "AUTHORIZE_TRANSITION"
    raise ValueError("unknown mode")


def expected_next_generation(state):
    return int(state["active_generation"]) + 1
