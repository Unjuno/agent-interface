"""Audit preplanned MAP01 no-visible-effect contingencies and grouped admission."""
import json
from pathlib import Path

from map01_stagnation_v1 import descriptor, normalized_mae

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-contingency-v1"
OUT = HERE / "results/map01-contingency-v1-audit.json"
RECEIPT_AUDIT = HERE / "results/map01-effect-receipt-v1-audit.json"


def load(role: str) -> tuple[dict, dict, list[dict]]:
    root = ROOT / role
    report = json.loads((root / "report.json").read_text())
    environment = json.loads((root / "environment.json").read_text())
    events = [json.loads(line) for line in (root / "plan-events.jsonl").read_text().splitlines()]
    return report, environment, events


def metrics(report: dict) -> dict:
    usage_keys = ("input_tokens", "cached_input_tokens", "output_tokens",
                  "reasoning_output_tokens")
    usage = {key: sum(row["usage"][key] for row in report["decisions"])
             for key in usage_keys}
    score = report["score"]
    return {
        "iterations": report["iterations"],
        "map_exit": score["map_exit"],
        "death_count": score["death_count"],
        "kill_count": score["kill_count"],
        "wall_seconds": score["wall_control_ns"] / 1e9,
        "model_seconds": report["model_wall_seconds"],
        "nonmodel_seconds": score["wall_control_ns"] / 1e9 - report["model_wall_seconds"],
        "contingencies_authored": report["contingencies_authored"],
        "branches_taken": report["contingency_branches_taken"],
        "branch_latency_ms": report["contingency_branch_latency_ms"],
        "program_admissions": report["program_admissions"],
        "extra_program_admissions_vs_one_bundle":
            report["extra_program_admissions_vs_one_bundle"],
        "receipt_commands": report["effect_receipt_commands"],
        "receipt_samples": report["effect_observation_samples"],
        "receipt_capture_ms": report["effect_observation_capture_ms"],
        "usage": {**usage,
                  "uncached_input_tokens": usage["input_tokens"] - usage["cached_input_tokens"]},
    }


def validate_trace(report: dict, events: list[dict]) -> None:
    accepted_ids = [row["id"] for row in events if row.get("event") == "accepted"]
    assert len(accepted_ids) == report["program_admissions"]
    assert len(set(accepted_ids)) == len(accepted_ids)
    for decision in report["decisions"]:
        if decision["action"]["state"] != "active":
            continue
        trace = decision["execution_trace"]
        primary = [row for row in trace if row["role"] == "primary"]
        branch = decision["contingency_branch"]
        expected_primary = len(decision["action"]["commands"])
        if branch:
            expected_primary = branch["after_command"] + 1
            fallback = [row["command"] for row in trace if row["role"] == "fallback"]
            assert fallback == branch["fallback_commands"]
            trigger = primary[-1]["receipt"]
            assert trigger["result"] == "no_visible_effect"
            first_fallback = next(row for row in trace if row["role"] == "fallback")
            observed_latency = ((first_fallback["accepted_ns"] - trigger["effect_observed_ns"])
                                / 1e6)
            assert abs(observed_latency - branch["latency_ms"]) < 1e-6
        assert len(primary) == expected_primary
        assert [row["command"] for row in primary] == decision["action"]["commands"][:expected_primary]


def main() -> None:
    ungrouped, env_a, events_a = load("ungrouped")
    grouped, env_b, events_b = load("grouped")
    fixed = ("vizdoom", "mode", "ticrate", "seed", "map", "skill",
             "scenario_path", "iwad_sha256", "sound_for_controller",
             "episode_timeout_seconds")
    assert {key: env_a[key] for key in fixed} == {key: env_b[key] for key in fixed}
    initial_mae = normalized_mae(descriptor(ROOT / "ungrouped/frames/00.png"),
                                 descriptor(ROOT / "grouped/frames/00.png"))
    assert initial_mae <= 0.015
    for report, events in ((ungrouped, events_a), (grouped, events_b)):
        assert report["model"] == "gpt-5.6-luna" and report["effort"] == "low"
        assert report["iterations"] == 12 and report["model_session_span"] == 4
        assert report["score"]["death_count"] == 0 and not report["score"]["map_exit"]
        assert report["contingency_branches_taken"] == 1
        validate_trace(report, events)
    assert ungrouped["program_admissions"] == 18
    assert ungrouped["extra_program_admissions_vs_one_bundle"] == 6
    assert grouped["program_admissions"] == 13
    assert grouped["extra_program_admissions_vs_one_bundle"] == 1
    assert grouped["contingency_branch_latency_ms"][0] < 100
    prior = json.loads(RECEIPT_AUDIT.read_text())
    prior_latency = prior["long_compact"]["effect_receipts"][
        "median_no_effect_observation_to_next_plan_accept_ms"]
    local_latency = grouped["contingency_branch_latency_ms"][0]
    result = {
        "status": "passed",
        "protocol": {
            "seed": 990609,
            "same_model_effort_task_environment_iterations_session_span": True,
            "initial_descriptor_normalized_mae": initial_mae,
            "initial_descriptor_below_no_visible_effect_threshold": True,
            "allocation_limit": "two sequential 12-decision feasibility runs; model outputs and ASYNC timing are nondeterministic",
            "iwad_paths_differ_but_sha256_matches": True,
        },
        "ungrouped": metrics(ungrouped),
        "grouped": metrics(grouped),
        "grouping_delta": {
            "program_admissions": grouped["program_admissions"] - ungrouped["program_admissions"],
            "extra_admissions": (grouped["extra_program_admissions_vs_one_bundle"] -
                                 ungrouped["extra_program_admissions_vs_one_bundle"]),
            "receipt_capture_ms": (grouped["effect_observation_capture_ms"] -
                                   ungrouped["effect_observation_capture_ms"]),
        },
        "latency_reference": {
            "prior_no_effect_to_next_model_plan_median_ms": prior_latency,
            "grouped_local_branch_ms": local_latency,
            "observed_path_ratio": prior_latency / local_latency,
            "scope": "reference median from three prior events versus one local branch; not a population speedup estimate",
        },
        "observed_result": "a real no-visible-effect branch ran a model-authored fallback locally; contingency-boundary grouping removed five unused admissions and retained sub-100ms branch admission",
        "decision": "retain as local contingency mechanism feasibility; completion and false-branch quality remain unproven",
        "retained_failures": json.loads((ROOT / "failures.json").read_text()),
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
