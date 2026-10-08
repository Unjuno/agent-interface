"""Emit a small explicit transition-uncertainty semantics table."""
import itertools
import json
import sys
from pathlib import Path


LIFETIMES = ("FULL", "ZERO", "EVENT")
ORDERS = ("NATURE_FIRST", "AGENT_FIRST")
EVIDENCE = ("VALID", "MISSING_OR_STALE")


def histories(lifetime):
    """All three-step binary nature assignments under the named freeze rule."""
    if lifetime == "FULL":
        return [[x, x, x] for x in (0, 1)]
    if lifetime == "ZERO":
        return [list(xs) for xs in itertools.product((0, 1), repeat=3)]
    if lifetime == "EVENT":
        # Two pre-event assignments may differ; after the event the second
        # assignment is fixed for the remainder of the episode.
        return [[x, y, y] for x in (0, 1) for y in (0, 1)]
    raise ValueError(lifetime)


def main(path):
    rows = []
    for lifetime in LIFETIMES:
        for order in ORDERS:
            for evidence in EVIDENCE:
                hs = histories(lifetime)
                # A missing/stale receipt cannot eliminate any possible history.
                retained = hs if evidence == "MISSING_OR_STALE" else hs
                rows.append({"lifetime": lifetime, "order": order,
                             "evidence": evidence, "histories": retained,
                             "agent_information": "action+public-observation",
                             "nature_information": ("action+public-observation"
                                 if order == "AGENT_FIRST" else "public-observation"),
                             "unsafe_admission": False})
    # Negative control: if transitions ignore the uncertainty variable,
    # all variants have the same singleton safe-effect set.
    control = [{"lifetime": l, "order": o, "effect_set": ["SAFE"]}
               for l in LIFETIMES for o in ORDERS]
    Path(path).write_text(json.dumps({"schema": "issue-6580-t0-candidate-v1",
        "rows": rows, "negative_control": control}, sort_keys=True,
        separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
