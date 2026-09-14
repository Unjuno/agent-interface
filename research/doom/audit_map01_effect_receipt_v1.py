"""Audit same-seed command-effect receipt feasibility and prompt compression."""
import json
import statistics
from pathlib import Path

from map01_stagnation_v1 import descriptor, find_revisit, normalized_mae

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-effect-receipt-v1"
OUT = HERE / "results/map01-effect-receipt-v1-audit.json"


def arm(role: str) -> tuple[dict, dict, list]:
    root = ROOT / role
    report = json.loads((root / "report.json").read_text())
    environment = json.loads((root / "environment.json").read_text())
    events = [json.loads(line) for line in (root / "plan-events.jsonl").read_text().splitlines()]
    return report, environment, events


def metrics(role: str, report: dict, events: list) -> dict:
    decisions = report["decisions"]
    usage_keys = ("input_tokens", "cached_input_tokens", "output_tokens",
                  "reasoning_output_tokens")
    usages = {key: sum(row["usage"][key] for row in decisions) for key in usage_keys}
    first_feedback = []
    command_first_feedback = []
    command_effect_endpoint = []
    for row in decisions:
        identifier = f"plan-{row['iteration']}"
        accepted = next(event["accepted_ns"] for event in events
                        if event.get("event") == "accepted" and event.get("id") == identifier)
        for step in range(len(row["action"]["commands"])):
            samples = [event for event in events if event.get("event") == "observation"
                       and event.get("id") == identifier and event.get("step") == step]
            assert samples
            first_feedback.append((samples[0]["capture_ns"] - accepted) / 1e6)
            issued = next(event["issued_ns"] for event in events
                          if event.get("event") == "step_started"
                          and event.get("id") == identifier and event.get("step") == step)
            command_first_feedback.append((samples[0]["capture_ns"] - issued) / 1e6)
            command_effect_endpoint.append((samples[-1]["capture_ns"] - issued) / 1e6)
    receipts = [receipt for row in decisions for receipt in row.get("effect_receipts", [])]
    history = []
    revisit_count = 0
    for index in range(len(decisions)):
        frame = descriptor(ROOT / role / "frames" / f"{index:02d}.png")
        revisit_count += find_revisit(frame, history) is not None
        history.append(frame)
    result = {
        "map_exit": report["score"]["map_exit"],
        "death_count": report["score"]["death_count"],
        "kill_count": report["score"]["kill_count"],
        "iterations": len(decisions),
        "wall_seconds": report["score"]["wall_control_ns"] / 1e9,
        "model_seconds": report["model_wall_seconds"],
        "nonmodel_seconds": report["score"]["wall_control_ns"] / 1e9 - report["model_wall_seconds"],
        "median_model_seconds": statistics.median(row["model_ns"] / 1e9 for row in decisions),
        "plan_observations": sum(event.get("event") == "observation" for event in events),
        "median_accept_to_first_hold_observation_ms": statistics.median(first_feedback),
        "median_command_issue_to_first_visual_feedback_ms": statistics.median(command_first_feedback),
        "median_command_issue_to_effect_endpoint_ms": statistics.median(command_effect_endpoint),
        "revisit_detections": revisit_count,
        "usage": {**usages, "uncached_input_tokens": usages["input_tokens"] - usages["cached_input_tokens"]},
    }
    if receipts:
        no_effect_to_next_plan = []
        for row in decisions[:-1]:
            for receipt in row.get("effect_receipts", []):
                if receipt["result"] != "no_visible_effect":
                    continue
                observed = next(event["capture_ns"] for event in events
                                if event.get("event") == "observation"
                                and event.get("sequence") == receipt["after_sequence"])
                next_accepted = next(event["accepted_ns"] for event in events
                                     if event.get("event") == "accepted"
                                     and event.get("id") == f"plan-{row['iteration'] + 1}")
                no_effect_to_next_plan.append((next_accepted - observed) / 1e6)
        result["effect_receipts"] = {
            "commands": len(receipts),
            "hold_samples_reused": sum(receipt["samples"] for receipt in receipts),
            "capture_ms": report["effect_observation_capture_ms"],
            "no_visible_effect": sum(receipt["result"] == "no_visible_effect" for receipt in receipts),
            "extra_steps": report["effect_receipt_extra_steps"],
            "median_no_effect_observation_to_next_plan_accept_ms":
                statistics.median(no_effect_to_next_plan) if no_effect_to_next_plan else None,
        }
    return result


def main() -> None:
    arms = {role: arm(role) for role in ("baseline", "verbose", "compact")}
    long_arms = {role: arm(role) for role in ("long-baseline", "long-compact")}
    fixed_keys = ("vizdoom", "mode", "ticrate", "seed", "map", "skill",
                  "scenario_path", "iwad_sha256", "sound_for_controller",
                  "episode_timeout_seconds")
    for group in (arms, long_arms):
        environments = [value[1] for value in group.values()]
        assert all({key: env[key] for key in fixed_keys} ==
                   {key: environments[0][key] for key in fixed_keys}
                   for env in environments[1:])
    for report, _, _ in arms.values():
        assert report["model"] == "gpt-5.6-luna" and report["effort"] == "low"
        assert report["model_session_span"] == 4 and len(report["decisions"]) == 12
        assert not report["score"]["map_exit"] and report["score"]["death_count"] == 0
    for report, _, _ in long_arms.values():
        assert report["model"] == "gpt-5.6-luna" and report["effort"] == "low"
        assert report["model_session_span"] == 4 and len(report["decisions"]) == 40
        assert not report["score"]["map_exit"] and report["score"]["death_count"] == 0
    frames = [descriptor(ROOT / role / "frames/00.png")
              for role in ("baseline", "verbose", "compact")]
    assert normalized_mae(frames[0], frames[1]) == 0
    assert normalized_mae(frames[0], frames[2]) == 0
    assert normalized_mae(descriptor(ROOT / "long-baseline/frames/00.png"),
                          descriptor(ROOT / "long-compact/frames/00.png")) == 0

    verbose = arms["verbose"][0]
    full_chars = compact_chars = 0
    for index in range(len(verbose["decisions"])):
        prior = [] if index == 0 else verbose["decisions"][index - 1].get("effect_receipts", [])
        full_chars += len(json.dumps({"scope": "previous program viewport effects only",
                                     "receipts": prior}, separators=(",", ":")))
        compact_chars += len(json.dumps([receipt["action"] for receipt in prior
                                        if receipt["result"] == "no_visible_effect"],
                                       separators=(",", ":")))
    compact_report = arms["compact"][0]
    exposed = [row for row in compact_report["decisions"] if row.get("effect_memory")]
    assert len(exposed) == 3
    assert all(not set(row["effect_memory"]) &
               {command["action"] for command in row["action"]["commands"]}
               for row in exposed)

    result = {
        "status": "passed",
        "protocol": {
            "order": ["verbose_receipt", "baseline", "compact_receipt"],
            "seed": 990608,
            "same_model_effort_task_environment_iterations_session_span": True,
            "initial_descriptors_identical": True,
            "allocation_limit": "one ordered three-arm 12-decision feasibility allocation; no completion comparison",
        },
        "baseline": metrics("baseline", arms["baseline"][0], arms["baseline"][2]),
        "verbose": metrics("verbose", arms["verbose"][0], arms["verbose"][2]),
        "compact": metrics("compact", arms["compact"][0], arms["compact"][2]),
        "planner_projection": {
            "verbose_dynamic_receipt_characters": full_chars,
            "compact_dynamic_receipt_characters": compact_chars,
            "character_reduction_percent": (full_chars - compact_chars) / full_chars * 100,
            "compact_no_effect_exposures": len(exposed),
            "compact_immediate_repeats_of_exposed_action": 0,
        },
        "observed_result": "existing hold samples provide roughly 64-68ms first visual feedback without extra steps; compact projection preserved planner response with 0.84% more total input tokens than baseline, but task improvement is unproven",
        "decision": "retain as effect-receipt feasibility; require a longer matched task comparison before promotion",
    }
    long_baseline = metrics("long-baseline", long_arms["long-baseline"][0], long_arms["long-baseline"][2])
    long_compact = metrics("long-compact", long_arms["long-compact"][0], long_arms["long-compact"][2])
    long_exposed = [row for row in long_arms["long-compact"][0]["decisions"]
                    if row.get("effect_memory")]
    long_repeats = sum(bool(set(row["effect_memory"]) &
                            {command["action"] for command in row["action"]["commands"]})
                       for row in long_exposed)
    result["long_protocol"] = {
        "order": ["baseline", "compact_receipt"],
        "seed": 990609,
        "same_model_effort_task_environment_iterations_session_span": True,
        "initial_descriptors_identical": True,
        "allocation_limit": "one ordered 40-decision pair; ASYNC timing and model outputs are not deterministic",
    }
    result["long_baseline"] = long_baseline
    result["long_compact"] = long_compact
    result["long_delta_compact_vs_baseline"] = {
        "wall_percent": (long_compact["wall_seconds"] / long_baseline["wall_seconds"] - 1) * 100,
        "model_percent": (long_compact["model_seconds"] / long_baseline["model_seconds"] - 1) * 100,
        "nonmodel_percent": (long_compact["nonmodel_seconds"] / long_baseline["nonmodel_seconds"] - 1) * 100,
        "input_tokens_percent": (long_compact["usage"]["input_tokens"] / long_baseline["usage"]["input_tokens"] - 1) * 100,
        "uncached_input_tokens_percent": (long_compact["usage"]["uncached_input_tokens"] / long_baseline["usage"]["uncached_input_tokens"] - 1) * 100,
        "no_effect_exposures": len(long_exposed),
        "immediate_repeats_of_exposed_action": long_repeats,
    }
    result["long_observed_result"] = "both arms were unfinished with zero deaths and kills; compact receipts changed immediate actions but did not reduce revisit detections"
    result["decision"] = "retain as effect-receipt feasibility; do not claim or promote a gameplay gain"
    assert result["verbose"]["effect_receipts"]["commands"] == 21
    assert result["compact"]["effect_receipts"]["commands"] == 19
    assert result["compact"]["effect_receipts"]["extra_steps"] == 0
    assert result["long_compact"]["effect_receipts"]["commands"] == 64
    assert result["long_delta_compact_vs_baseline"]["no_effect_exposures"] == 3
    assert result["long_delta_compact_vs_baseline"]["immediate_repeats_of_exposed_action"] == 0
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
