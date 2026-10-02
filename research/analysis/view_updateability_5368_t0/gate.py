"""Candidate finite observation-fiber actionability gate (stdlib only)."""
from __future__ import annotations

import json
from pathlib import Path


def run_case(case: dict) -> dict:
    if case["unknown_model"]:
        return {"id": case["id"], "decision": "UNKNOWN_MODEL", "hint": None, "fiber": []}

    observed = case["observed"]
    fiber = [
        world for world in case["worlds"]
        if all(world["fields"].get(key, object()) == value for key, value in observed.items())
    ]
    if not fiber:
        return {"id": case["id"], "decision": "UNKNOWN_MODEL", "hint": None, "fiber": []}

    def safe(world: dict) -> bool:
        effect = world["effects"].get(case["action"], {})
        return (
            effect.get("realizable") is True
            and effect.get("effect") == case["requested_effect"]
            and effect.get("target") == case["requested_target"]
            and not set(effect.get("collateral", ())).intersection(case["forbidden_collateral"])
        )

    labels = {world["id"]: safe(world) for world in fiber}
    if all(labels.values()):
        decision, hint = "ADMIT", None
    elif any(labels.values()):
        decision, hint = "NEEDS_DISAMBIGUATING_OBSERVATION", None
        for field in case["hint_candidates"]:
            partitions: dict[str, set[bool]] = {}
            for world in fiber:
                value = json.dumps(world["fields"].get(field, "<MISSING>"), sort_keys=True)
                partitions.setdefault(value, set()).add(labels[world["id"]])
            outcomes = set().union(*partitions.values())
            if len(partitions) > 1 and all(len(partition) == 1 for partition in partitions.values()) and len(outcomes) == 2:
                hint = field
                break
        if hint is None:
            decision = "UNTRANSLATABLE"
    else:
        decision, hint = "UNTRANSLATABLE", None

    return {
        "id": case["id"],
        "decision": decision,
        "hint": hint,
        "fiber": sorted(world["id"] for world in fiber),
    }


def run_baseline(case: dict) -> dict:
    label_matches = case["observed"].get("label") == case["requested_label"]
    admitted = case["freshness_valid"] is True and label_matches
    return {
        "id": case["id"],
        "decision": "ADMIT" if admitted else "YIELD",
        "freshness_pass": case["freshness_valid"] is True,
        "label_match": label_matches,
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    output = root / "candidate.jsonl"
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        for case in fixture["cases"]:
            stream.write(json.dumps(run_case(case), sort_keys=True, separators=(",", ":")) + "\n")
    with (root / "baseline.jsonl").open("x", encoding="utf-8", newline="\n") as stream:
        for case in fixture["cases"]:
            stream.write(json.dumps(run_baseline(case), sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()

