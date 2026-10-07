#!/usr/bin/env python3
"""Candidate generic-information/repeated-branch arms for #5309 A02."""
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def entropy(probabilities):
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


def main():
    fixture_bytes = (ROOT / "fixture.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    prior = fixture["prior"]
    before = entropy(prior.values())
    groups = {}
    for state, probability in prior.items():
        observation = fixture["mode_observation"][state]
        groups[observation] = groups.get(observation, 0.0) + probability
    after = sum(
        mass * entropy(
            [p / mass for state, p in prior.items() if fixture["mode_observation"][state] == obs]
        )
        for obs, mass in groups.items()
    )

    repeat_count = fixture["repeat_count"]
    raw = {
        "allocation": fixture["allocation"],
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "scope": "finite synthetic policy comparison; no GUI or live effect",
        "generic_one_step": {
            "proposal": "probe_mode",
            "admitted": True,
            "executed": "probe_mode",
            "observation": "mode0",
            "entropy_before_bits": round(before, 12),
            "expected_entropy_after_bits": round(after, 12),
            "information_gain_bits": round(before - after, 12),
            "naive_confidence": "PROMOTE_AFTER_INFORMATION_GAIN",
            "authority_granted": False,
        },
        "repeated_benign_branch": {
            "events": [
                {
                    "proposal": "repeat",
                    "admitted": True,
                    "executed": "repeat",
                    "observation": "routine",
                    "task_progress": True,
                    "opportunity_slot": fixture["exogenous_opportunity_stream"][i % 2],
                }
                for i in range(repeat_count)
            ],
            "naive_confidence": "PROMOTE_AFTER_REPEATED_SUCCESS",
            "authority_granted": False,
        },
        "planned_probe_sequences": fixture["planned_probe_sequences"],
        "refused_action_event": {
            "proposal": "witness",
            "admitted": False,
            "executed": None,
            "observation": None,
            "reason": "expired_before_step_1",
        },
        "exogenous_opportunity_stream": fixture["exogenous_opportunity_stream"],
        "no_action_counterfactual": {
            "proposal": None,
            "admitted": False,
            "executed": None,
            "observation": None,
            "opportunities_preserved": len(fixture["exogenous_opportunity_stream"]),
        },
        "authority_granted": False,
        "forbidden_effects": [],
    }
    encoded = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    raw["raw_sha256"] = hashlib.sha256(encoded).hexdigest()
    print(json.dumps(raw, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
