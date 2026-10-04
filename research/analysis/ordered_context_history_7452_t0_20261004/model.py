"""Frozen finite fixture for Issue #7452; one row is one reset episode."""

CONTEXTS = tuple((focus, surface, freshness)
                 for focus in (0, 1)
                 for surface in (0, 1)
                 for freshness in (0, 1))
EVENTS = ("OBSERVE", "REVOKE", "ACT", "RELEASE")


def legal(history):
    """Syntactic event-request histories; RELEASE requires prior ACT."""
    if not 1 <= len(history) <= 3 or any(event not in EVENTS for event in history):
        return False
    acted = False
    released = False
    for event in history:
        if event == "ACT":
            if released:
                return False
            acted = True
        elif event == "RELEASE":
            if not acted or released:
                return False
            released = True
    return True


PAIR_HISTORIES = tuple((a, b) for a in EVENTS for b in EVENTS if legal((a, b)))
PAIR_CONTEXTS = ((0, 0), (0, 1), (1, 0), (1, 1))


def context_cover():
    """Four-row binary strength-2 covering array over three context factors."""
    return ((0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0))


def joint_mutant(context, history):
    return context[0] == 1 and context[1] == 1 and history == ("REVOKE", "ACT")


def factor_mutant(context, history):
    return context[0] == 1 and history == ("OBSERVE", "OBSERVE")


def order_mutant(context, history):
    return history == ("REVOKE", "ACT")


def order_invariant_control(context, history):
    return context[1] == 1 and history[0] == "OBSERVE"
