"""Finite policy comparison for Issue #6680; standard library only."""

import json
import sys
from pathlib import Path


FIXTURE = Path(__file__).with_name("fixture.json")


def diagnose(fixture, case):
    probe = fixture["probe"]
    if not case["probe_admissible"] or not probe["admissible"] or probe["effectful"] or probe["lease_extension"]:
        return None, 0
    observed = case["observed"]
    hypotheses = [
        h for h, outcomes in probe["response_sets"].items()
        if observed in outcomes
    ]
    if len(hypotheses) != 1 or observed == "unsupported":
        return None, 1
    recovery = {"H_OBSERVATION": "reobserve", "H_DYNAMICS": "reset"}.get(hypotheses[0])
    return recovery, 1


def choose(fixture, case, policy):
    if policy == "always_reobserve":
        return "reobserve", 1
    if policy == "always_reset":
        return "reset", 0
    if policy == "immediate_yield":
        return "yield", 0
    if policy == "bounded_diagnose":
        action, observations = diagnose(fixture, case)
        return action or "yield", observations
    raise ValueError(f"unknown policy: {policy}")


def run(fixture=None):
    if fixture is None:
        fixture = json.loads(FIXTURE.read_text())
    rows = []
    for case in fixture["cases"]:
        for policy in fixture["policies"]:
            action, observations = choose(fixture, case, policy)
            rows.append({
                "case_id": case["id"],
                "policy": policy,
                "action": action,
                "diagnostic_observations": observations,
                "release_tick": fixture["pre_diagnosis_release_tick"],
                "forbidden_transition": False,
            })
    return {"schema": "safe-discriminating-observation-6680-raw-v1", "rows": rows}


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("candidate.raw.json")
    output.write_text(json.dumps(run(), sort_keys=True, indent=2) + "\n")
    print(json.dumps({"rows": len(run()["rows"]), "output": str(output)}))
