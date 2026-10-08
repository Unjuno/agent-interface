"""Public-model decision rule; deliberately has no hidden-state input."""

FAMILIES = {"separable", "action_equivalent", "impossible", "stale", "convergent"}
ARMS = {"no_probe", "one_step", "adaptive"}


def next_step(family: str, arm: str, observations: list[str], probes: list[str]) -> str:
    if family not in FAMILIES or arm not in ARMS:
        return "YIELD"
    if not observations or observations[0] != "READY":
        return "YIELD"

    if family == "action_equivalent":
        if arm == "one_step" and "P" not in probes:
            return "PROBE_P"
        return "ACT_COMMON"

    if family == "convergent" and arm == "adaptive":
        if "P" not in probes:
            return "PROBE_P"
        if "Q" not in probes:
            return "PROBE_Q"
        return "ACT_COMMON" if observations[-1] == "BOTH" else "YIELD"

    if arm == "no_probe":
        return "YIELD"
    if arm == "one_step":
        return "PROBE_P" if "P" not in probes else "YIELD"

    if "P" not in probes:
        return "PROBE_P"
    if "Q" not in probes:
        return "PROBE_Q"

    terminal = observations[-1]
    if terminal == "LEFT":
        return "ACT_LEFT"
    if terminal == "RIGHT":
        return "ACT_RIGHT"
    return "YIELD"
