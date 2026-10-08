"""Finite T0 candidate for Issue #8399; emits a reset-aware mixed suite."""
from itertools import product

CONTEXTS = tuple(product((0, 1), repeat=3))
HISTORIES = (
    ("OBSERVE", "ACT", "RELEASE"),
    ("OBSERVE", "REVOKE", "ACT", "RELEASE"),
)
EPISODES = tuple((context, history) for context in CONTEXTS for history in HISTORIES)

# For each (focus_generation, surface_mode) pair, include one context stratum
# and one history with REVOKE immediately followed by ACT before RELEASE.
SUITE = tuple(
    (next(context for context in CONTEXTS if context[:2] == pair),
     ("OBSERVE", "REVOKE", "ACT", "RELEASE"))
    for pair in product((0, 1), repeat=2)
)

if __name__ == "__main__":
    print({"episodes": len(EPISODES), "suite": SUITE})
