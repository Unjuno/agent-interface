"""Frozen finite contract for successor #6749 (candidate-side only)."""
import itertools

CHECKS = ("check_a", "check_b")
GENERATIONS = ("CURRENT", "INVALID")
OPTIONAL_PATHS = {
    "complete": ("optional_clear", "optional_complete"),
    "conflict": ("optional_clear", "optional_conflict"),
    "timeout": ("optional_clear", "optional_timeout"),
}
RESULTS = ("PASS", "FAIL")


def worlds():
    for a, b, generation, path_name in itertools.product(
        RESULTS, RESULTS, GENERATIONS, OPTIONAL_PATHS
    ):
        yield {
            "check_a": a,
            "check_b": b,
            "generation": generation,
            "optional_path": path_name,
            "events": ("check_a_" + a.lower(), "check_b_" + b.lower(),
                       "generation_" + generation.lower(), *OPTIONAL_PATHS[path_name]),
        }


def event_orders(events):
    """Interleave checks/generation with an indivisible, ordered optional path."""
    optional = events[3:]
    for order in itertools.permutations(events):
        observed_optional = tuple(event for event in order if event.startswith("optional_"))
        if observed_optional == optional:
            yield order


def state_after(world, prefix):
    observed = {"check_a": None, "check_b": None, "generation": None, "optional": "OPEN"}
    for event in prefix:
        if event.startswith("check_a_"):
            observed["check_a"] = event.removeprefix("check_a_").upper()
        elif event.startswith("check_b_"):
            observed["check_b"] = event.removeprefix("check_b_").upper()
        elif event.startswith("generation_"):
            observed["generation"] = event.removeprefix("generation_").upper()
        elif event == "optional_clear":
            observed["optional"] = "CLEARED"
        elif event == "optional_complete":
            observed["optional"] = "COMPLETE"
        elif event == "optional_conflict":
            observed["optional"] = "CONFLICT"
        elif event == "optional_timeout":
            observed["optional"] = "TIMEOUT"
    return observed


def disposition(observed):
    if observed["generation"] == "INVALID":
        return "INVALID"
    if observed["generation"] == "CURRENT" and "FAIL" in (
        observed["check_a"], observed["check_b"]
    ):
        return "STABLE_FAIL"
    if (observed["generation"] == "CURRENT"
            and observed["check_a"] == observed["check_b"] == "PASS"
            and observed["optional"] == "COMPLETE"):
        return "PASS"
    return "PROVISIONAL"


def pending(observed):
    todo = [name for name in CHECKS if observed[name] is None]
    if observed["generation"] is None:
        todo.append("source_frontier:generation")
    if observed["optional"] not in ("COMPLETE", "CONFLICT", "TIMEOUT"):
        todo.append("source_frontier:optional")
    return todo


def all_prefixes():
    """Return one row per legal event-order prefix; duplicate states remain distinct."""
    rows = []
    for wi, world in enumerate(worlds()):
        wid = f"w{wi:02d}"
        for order in event_orders(world["events"]):
            for n in range(len(order) + 1):
                prefix = order[:n]
                state = state_after(world, prefix)
                rows.append({"world_id": wid, "prefix": list(prefix), "state": state,
                             "disposition": disposition(state),
                             "pending_obligations": pending(state)})
    return rows
