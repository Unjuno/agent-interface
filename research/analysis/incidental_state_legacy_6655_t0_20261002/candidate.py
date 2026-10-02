"""One-shot finite candidate generator for the Issue #6655 T0 fixture."""

import hashlib
import json
import random
import sys
from pathlib import Path

import fixture


def _merge(left, right):
    state = dict(left)
    state.update(right)
    return state


def _outcome(case, state):
    case_id = case["case_id"]
    if case_id == "helpful_incidental_view":
        observations = 1 if state["view"] == "target_focused" else 3
        return {"correct": True, "observations": observations, "recovery_cost": 0}
    if case_id == "harmful_stale_filter":
        hidden = state["filter"] == "stale_hides_required_cue"
        return {"correct": not hidden, "observations": 1 if hidden else 3, "recovery_cost": 2 if hidden else 0}
    if case_id == "irrelevant_theme":
        return {"correct": True, "observations": 2, "recovery_cost": 0}
    if case_id == "required_saved_effect":
        return {"correct": state["saved_record"] is True, "observations": 2, "recovery_cost": 0}
    raise ValueError("ineligible cases have no scored outcome")


def build_records():
    rows = []
    for case_index, case in enumerate(fixture.CASES):
        for seed in fixture.SEEDS:
            rng_seed = 0x6655 ^ (seed * 1009) ^ (case_index * 9176)
            order = ["inherit", "reset"]
            random.Random(rng_seed).shuffle(order)
            origin_before = dict(case["baseline"])
            origin_after = _merge(origin_before, case["delta"])
            state_diff = [
                {"field": field, "before": origin_before.get(field), "after": after,
                 "classification": case["classification"]}
                for field, after in sorted(case["delta"].items())
            ]
            arms = []
            for rank, arm_name in enumerate(order):
                later_seed = seed + (case.get("reset_seed_offset", 0) if arm_name == "reset" else 0)
                if not case["eligible"]:
                    state = dict(origin_after)
                    if arm_name == "reset" and case["case_id"] == "incomplete_restoration":
                        state = dict(origin_after)  # Deliberately fails the reset-completeness gate.
                    restoration = {
                        "attempted": arm_name == "reset",
                        "complete": arm_name != "reset" or case["case_id"] != "incomplete_restoration",
                        "cost": 0,
                    }
                    outcome = None
                else:
                    if arm_name == "inherit":
                        state = dict(origin_after)
                        restoration = {"attempted": False, "complete": True, "cost": 0}
                    elif case["classification"] == "required_effect":
                        # Reset incidental state only; preserve the originating task's required effect.
                        state = _merge(case["baseline"], case["delta"])
                        restoration = {"attempted": True, "complete": True, "cost": 0}
                    else:
                        state = dict(case["baseline"])
                        restoration = {"attempted": True, "complete": True, "cost": 1}
                    outcome = _outcome(case, state)
                    outcome["total_cost"] = outcome["observations"] + outcome["recovery_cost"] + restoration["cost"]
                arms.append({
                    "arm": arm_name,
                    "assignment_rank": rank,
                    "later_task_seed": later_seed,
                    "later_task_id": case["task"]["id"],
                    "state_after_treatment": state,
                    "restoration": restoration,
                    "outcome": outcome,
                })
            rows.append({
                "case_id": case["case_id"],
                "seed": seed,
                "randomization_seed": rng_seed,
                "assignment_order": order,
                "origin_state_before": origin_before,
                "origin_state_after": origin_after,
                "state_diff": state_diff,
                "task_contract": dict(case["task"]),
                "origin_task_outcome": {
                    "completed": True,
                    "required_effects": dict(case["task"].get("required_effect", {})),
                },
                "eligible": case["eligible"],
                "exclusion_reason": case.get("exclusion_reason"),
                "arms": arms,
            })
    return {
        "schema": "issue6655-incidental-state-t0-v1",
        "base_main_sha": fixture.BASE_MAIN_SHA,
        "seeds": list(fixture.SEEDS),
        "case_ids": [case["case_id"] for case in fixture.CASES],
        "fixture_sha256": hashlib.sha256(Path(fixture.__file__).read_bytes()).hexdigest(),
        "rows": rows,
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("usage: candidate.py OUTPUT.json", file=sys.stderr)
        return 2
    output = Path(argv[0])
    raw = json.dumps(build_records(), sort_keys=True, separators=(",", ":")) + "\n"
    try:
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(raw)
    except FileExistsError:
        print("refusing to overwrite existing output", file=sys.stderr)
        return 3
    print(f"wrote {len(build_records()['rows'])} paired rows to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
