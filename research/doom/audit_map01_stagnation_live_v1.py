"""Audit the ordered same-seed v1 forced-recovery comparison."""
import json
import statistics
from pathlib import Path

from map01_stagnation_v1 import descriptor, find_revisit, normalized_mae, sustained_revisit

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-stagnation-live-v1"
OUT = HERE / "results/map01-stagnation-live-v1-audit.json"


def arm(role: str) -> tuple[dict, list, list]:
    root = ROOT / role
    report = json.loads((root / "report.json").read_text())
    frames = [descriptor(root / "frames" / f"{i:02d}.png")
              for i in range(len(report["decisions"]))]
    history = []
    revisits = []
    for i, frame in enumerate(frames):
        revisit = find_revisit(frame, history)
        if revisit:
            revisits.append({"iteration": i, **revisit})
        history.append(frame)
    return report, frames, revisits


def metrics(report: dict, revisits: list) -> dict:
    decisions = report["decisions"]
    usage_keys = ("input_tokens", "cached_input_tokens", "output_tokens",
                  "reasoning_output_tokens")
    revisit_set = {row["iteration"] for row in revisits}
    flags = []
    sustained = []
    for i in range(len(decisions)):
        flags.append(i in revisit_set)
        if sustained_revisit(flags):
            sustained.append(i)
    return {
        "map_exit": report["score"]["map_exit"],
        "death_count": report["score"]["death_count"],
        "kill_count": report["score"]["kill_count"],
        "iterations": len(decisions),
        "wall_seconds": report["score"]["wall_control_ns"] / 1e9,
        "model_seconds": report["model_wall_seconds"],
        "nonmodel_seconds": report["score"]["wall_control_ns"] / 1e9 - report["model_wall_seconds"],
        "median_model_seconds": statistics.median(row["model_ns"] / 1e9 for row in decisions),
        "revisit_detections": len(revisits),
        "counterfactual_sustained_advisory_iterations": sustained,
        "usage": {key: sum(row["usage"][key] for row in decisions) for key in usage_keys},
    }


def main() -> None:
    candidate, candidate_frames, candidate_revisits = arm("candidate")
    baseline, baseline_frames, baseline_revisits = arm("baseline")
    advisory, advisory_frames, advisory_revisits = arm("advisory")
    environments = [json.loads((ROOT / role / "environment.json").read_text())
                    for role in ("candidate", "baseline", "advisory")]
    fixed_keys = ("vizdoom", "mode", "ticrate", "seed", "map", "skill",
                  "scenario_path", "iwad_sha256", "sound_for_controller",
                  "episode_timeout_seconds")
    assert all({key: env[key] for key in fixed_keys} ==
               {key: environments[0][key] for key in fixed_keys}
               for env in environments[1:])
    for report in (candidate, baseline, advisory):
        assert report["model"] == "gpt-5.6-luna" and report["effort"] == "low"
        assert report["model_session_span"] == 4 and len(report["decisions"]) == 40
        assert report["score"]["skill"] == 1 and not report["score"]["map_exit"]
    assert candidate["score"]["map"] == baseline["score"]["map"] == "MAP01"
    assert candidate["stagnation_overrides"] == 10
    assert advisory["sustained_revisit_advisories"] == 12
    escaped = []
    for row in candidate["decisions"]:
        if not row.get("compiled_override"):
            continue
        i = row["iteration"]
        if i + 1 == len(candidate_frames):
            continue
        revisit = row["stagnation_revisit"]
        after = normalized_mae(candidate_frames[i + 1],
                               candidate_frames[revisit["prior_iteration"]])
        escaped.append(after > revisit["threshold"])
    result = {
        "status": "passed",
        "protocol": {
            "order": ["forced_recovery_candidate", "no_recovery_baseline",
                      "planner_advisory_candidate"],
            "seed": 990606,
            "same_model_effort_task_environment_iterations_session_span": True,
            "allocation_limit": "one ordered three-arm allocation; ASYNC timing and model outputs are not deterministic",
            "initial_descriptor_mae": normalized_mae(candidate_frames[0], baseline_frames[0]),
        },
        "candidate": metrics(candidate, candidate_revisits),
        "baseline": metrics(baseline, baseline_revisits),
        "advisory": metrics(advisory, advisory_revisits),
        "candidate_override_receipt": {
            "overrides": candidate["stagnation_overrides"],
            "next_observation_left_matched_cluster": sum(escaped),
            "eligible_next_observations": len(escaped),
        },
        "advisory_receipt": {
            "reported_sustained_advisories": advisory["sustained_revisit_advisories"],
            "model_assessments_acknowledging_revisit": sum(
                "revisit" in row["action"]["assessment"].lower()
                for row in advisory["decisions"]
                if row["visual_memory"]["status"] == "sustained_revisit"),
        },
        "observed_result": "neither forced recovery nor planner advisory improved MAP01 completion; both increased revisit detections versus the baseline in these ordered allocations",
        "decision": "retain both as failed candidates; next layer needs local action-effect receipts rather than another revisit directive",
    }
    assert result["candidate"]["counterfactual_sustained_advisory_iterations"] == [24, 25, 35, 36, 37]
    assert result["baseline"]["counterfactual_sustained_advisory_iterations"] == []
    assert result["advisory"]["revisit_detections"] == 18
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
