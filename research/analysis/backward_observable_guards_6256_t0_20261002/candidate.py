"""Candidate exact-preimage and observation-partition enumerator for Issue #6256."""
from __future__ import annotations

import itertools
import json
from pathlib import Path


def outcome_is_good(outcome: dict, model: dict) -> bool:
    return (
        outcome["terminated"] is True
        and outcome["steps"] <= model["horizon_steps"]
        and outcome["effect"] == model["required_effect"]
        and not set(outcome["forbidden_prefix"]).intersection(model["forbidden_prefix_tags"])
        and outcome["release"] == model["required_release"]
    )


def exact_preimage(model: dict) -> set[str]:
    """Universal total-correctness preimage: every declared outcome must pass."""
    return {
        state["id"]
        for state in model["states"]
        if state["outcomes"] and all(outcome_is_good(outcome, model) for outcome in state["outcomes"])
    }


def partition(states: list[dict], cues: tuple[str, ...]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = {}
    for state in states:
        signature = tuple(state["cues"][cue] for cue in cues)
        groups.setdefault(signature, []).append(state)
    return groups


def classify(group: list[dict], preimage: set[str]) -> str:
    flags = {state["id"] in preimage for state in group}
    if flags == {True}:
        return "ADMIT"
    if flags == {False}:
        return "REFUSE"
    return "UNKNOWN_NOT_OBSERVABLE"


def minimum_sufficient_cue_sets(model: dict, preimage: set[str]) -> list[list[str]]:
    """Find minimum cues for the predeclared verified-certificate stratum."""
    states = [s for s in model["states"] if s["cues"]["certificate_status"] == "verified"]
    cues = tuple(model["permitted_cues"])
    candidates = []
    for width in range(len(cues) + 1):
        for subset in itertools.combinations(cues, width):
            if all(len({s["id"] in preimage for s in group}) == 1 for group in partition(states, subset).values()):
                candidates.append(list(subset))
        if candidates:
            return candidates
    return []


def authored_guard_ids(model: dict) -> list[str]:
    return [
        s["id"] for s in model["states"]
        if s["cues"]["pixels"] == "save_visible"
        and s["layout_simple"] is True
        and s["cues"]["generation_fresh"] is True
    ]


def overstrong_guard_ids(model: dict, preimage: set[str]) -> list[str]:
    return [s["id"] for s in model["states"] if s["id"] in preimage and s["layout_simple"] is True]


def build_result(model: dict) -> dict:
    preimage = exact_preimage(model)
    groups = partition(model["states"], tuple(model["permitted_cues"]))
    decisions = [
        {"signature": list(signature), "state_ids": [s["id"] for s in group], "decision": classify(group, preimage)}
        for signature, group in sorted(groups.items(), key=lambda item: repr(item[0]))
    ]
    pixels_only = partition(model["states"], ("pixels",))
    alias_pair = [s for s in model["states"] if s["id"] in {"ready_simple", "already_committed"}]
    typed_pair = partition(alias_pair, ("pixels", "already_committed_fresh"))
    return {
        "model_id": model["model_id"],
        "horizon_steps": model["horizon_steps"],
        "preimage_state_ids": sorted(preimage),
        "state_count": len(model["states"]),
        "outcome_count": sum(len(s["outcomes"]) for s in model["states"]),
        "outcome_rows": [
            {"state_id": s["id"], "outcome": o, "passes_total_correctness": outcome_is_good(o, model)}
            for s in model["states"] for o in s["outcomes"]
        ],
        "full_cue_decisions": decisions,
        "verified_stratum_minimum_sufficient_cue_sets": minimum_sufficient_cue_sets(model, preimage),
        "full_model_global_sufficient_cue_set_exists": all(
            len({s["id"] in preimage for s in group}) == 1
            for group in partition(model["states"], tuple(model["permitted_cues"])).values()
        ),
        "pixel_only_ready_vs_committed": classify(pixels_only[("save_visible",)], preimage),
        "fresh_typed_commit_receipt_pair": {
            "signatures": [{"signature": list(sig), "decision": classify(group, preimage)} for sig, group in sorted(typed_pair.items(), key=lambda item: repr(item[0]))]
        },
        "authored_guard_state_ids": sorted(authored_guard_ids(model)),
        "authored_guard_unsafe_admissions": sorted(set(authored_guard_ids(model)) - preimage),
        "authored_guard_safe_rejections": sorted(preimage - set(authored_guard_ids(model))),
        "overstrong_guard_state_ids": sorted(overstrong_guard_ids(model, preimage)),
        "overstrong_guard_safe_rejections": sorted(preimage - set(overstrong_guard_ids(model, preimage))),
    }


def main() -> None:
    directory = Path(__file__).resolve().parent
    model = json.loads((directory / "MODEL.json").read_text(encoding="utf-8"))
    result = build_result(model)
    output = directory / "results" / "t0-01" / "candidate_raw.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": "CANDIDATE_COMPLETE", "state_count": result["state_count"], "outcome_count": result["outcome_count"], "preimage": result["preimage_state_ids"]}, sort_keys=True))


if __name__ == "__main__":
    main()
