"""Host-only exhaustive sensitivity probe for Issue #5531 T5.

The probe uses all ordered pairs of the eight leaves in a 2x2x2 hierarchy.
For each pair, it compares a candidate configured cut depth with each possible
latent common-cause boundary. It is a deterministic synthetic abstraction.
"""

import hashlib
import itertools
import json
import platform
import sys


SITES = ("site-a", "site-b")
RACKS = ("rack-1", "rack-2")
HOSTS = ("host-1", "host-2")
LEAVES = tuple(itertools.product(SITES, RACKS, HOSTS))
DEPTHS = (1, 2, 3)


def first_divergence(left, right):
    for index, (a, b) in enumerate(zip(left, right), start=1):
        if a != b:
            return index
    return None


def candidate_failed(divergence, configured_cut):
    # Two distinct observers reach the terminal-failure threshold iff their
    # paths differ at or above the configured (one-indexed) cut.
    return divergence is not None and divergence <= configured_cut


def oracle_failed(divergence, latent_boundary):
    # Ground truth under the declared synthetic model: a divergence at or
    # above the latent common-cause boundary is independent evidence.
    return divergence is not None and divergence <= latent_boundary


def main():
    pairs = list(itertools.product(LEAVES, repeat=2))
    matrix = []
    all_pairs = []
    for configured_cut in DEPTHS:
        for latent_boundary in DEPTHS:
            fp = fn = 0
            for left, right in pairs:
                divergence = first_divergence(left, right)
                predicted = candidate_failed(divergence, configured_cut)
                truth = oracle_failed(divergence, latent_boundary)
                fp += int(predicted and not truth)
                fn += int(truth and not predicted)
                all_pairs.append({
                    "left": left,
                    "right": right,
                    "divergence": divergence,
                    "configured_cut": configured_cut,
                    "latent_boundary": latent_boundary,
                    "predicted_failed": predicted,
                    "oracle_failed": truth,
                })
            matrix.append({
                "configured_cut": configured_cut,
                "latent_boundary": latent_boundary,
                "false_failed": fp,
                "missed_failed": fn,
            })

    semantic = {
        "schema": "issue-5531-t5-cut-sensitivity-v1",
        "leaf_count": len(LEAVES),
        "ordered_pair_count": len(pairs),
        "cut_depths": list(DEPTHS),
        "latent_boundaries": list(DEPTHS),
        "pair_evaluations": len(all_pairs),
        "matrix": matrix,
        "interpretation": (
            "Errors occur exactly when configured cut depth differs from the "
            "synthetic latent common-cause boundary."
        ),
    }
    canonical = json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()
    output = {
        "semantic": semantic,
        "semantic_sha256": hashlib.sha256(canonical).hexdigest(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "docker_used": False,
            "network_used": False,
            "candidate_invocations": 0,
            "synthetic_enumeration_invocations": 1,
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
