"""Create the exact ordinal-probability inputs and auditor-only latent worlds."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CUTS = [-1.5, -0.5, 0.5, 1.5]
LEVELS = [-1.2, -0.4, 0.4, 1.2]


def logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def probs(eta: float) -> list[float]:
    cumulative = [logistic(c - eta) for c in CUTS]
    return [cumulative[0], *(cumulative[i] - cumulative[i - 1] for i in range(1, 4)), 1.0 - cumulative[-1]]


def make_case(case_id: str, b_ref: float, b_cmp: float, mu_ref: float, mu_cmp: float,
              cmp_anchor_offsets: list[float]) -> dict:
    groups = {}
    for group, shift, mu, offsets in (
        ("reference", b_ref, mu_ref, [0.0] * 4),
        ("comparison", b_cmp, mu_cmp, cmp_anchor_offsets),
    ):
        groups[group] = {
            "anchors": [probs(level + offset - shift) for level, offset in zip(LEVELS, offsets)],
            "self": probs(mu - shift),
        }
    return {
        "case_id": case_id,
        "anchors": {
            group: [{"anchor_index": idx, "probabilities": p} for idx, p in enumerate(rows["anchors"])]
            for group, rows in groups.items()
        },
        "self": {
            group: {"probabilities": values["self"]}
            for group, values in groups.items()
        },
    }


def canonical_hash(value: object) -> str:
    blob = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def main() -> None:
    spec = {
        "categories": 5,
        "cutpoints": CUTS,
        "anchor_levels": LEVELS,
        "shift_min": -1.0,
        "shift_step": 0.001,
        "shift_steps": 2000,
        "self_min": -2.0,
        "self_step": 0.001,
        "self_steps": 4000,
        "threshold_shift_grid": [round(-1.0 + 0.001 * i, 3) for i in range(2001)],
        "self_location_grid": [round(-2.0 + 0.001 * i, 3) for i in range(4001)],
        "max_anchor_residual": 0.01,
    }
    assumed = make_case("anchor-fit", 0.0, 0.6, -0.2, 0.4, [0.0] * 4)
    nonuniform = make_case("nonuniform-vignette-shift", 0.0, 0.6, -0.2, 0.4, [-0.5, -0.2, 0.2, 0.5])
    candidate_input = {"schema": "8522-observations-v1", "spec": spec, "cases": [assumed, nonuniform]}
    observed_hash = canonical_hash(assumed)
    oracle = {
        "schema": "8522-auditor-oracle-v1",
        "worlds": [
            {
                "world": "equivalent-anchors-and-shifted-thresholds",
                "true_contrast": 0.6,
                "observed_input_sha256": observed_hash,
                "groups": {
                    "reference": {"threshold_shift": 0.0, "anchor_levels": LEVELS, "self_location": -0.2},
                    "comparison": {"threshold_shift": 0.6, "anchor_levels": LEVELS, "self_location": 0.4},
                },
            },
            {
                "world": "uniform-meaning-shift-violates-vignette-equivalence",
                "true_contrast": 0.0,
                "observed_input_sha256": observed_hash,
                "groups": {
                    "reference": {"threshold_shift": 0.0, "anchor_levels": LEVELS, "self_location": -0.2},
                    "comparison": {"threshold_shift": 0.0, "anchor_levels": [x - 0.6 for x in LEVELS], "self_location": -0.2},
                },
            },
        ],
    }
    (ROOT / "candidate_input.json").write_text(json.dumps(candidate_input, sort_keys=True, separators=(",", ":")) + "\n")
    (ROOT / "oracle.json").write_text(json.dumps(oracle, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
