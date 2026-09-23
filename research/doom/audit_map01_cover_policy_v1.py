"""Audit model-authored renewable cover policy and the retained compiler defect."""
import json
from pathlib import Path

from map01_stagnation_v1 import descriptor, normalized_mae

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-cover-policy-v1"
OUT = HERE / "results/map01-cover-policy-v1-audit.json"


def load(role: str) -> tuple[dict, dict, list[dict]]:
    root = ROOT / role
    report = json.loads((root / "report.json").read_text())
    environment = json.loads((root / "environment.json").read_text())
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    return report, environment, events


def cover_submits(events: list[dict]) -> dict[str, list[dict]]:
    return {row["command"]["id"]: row["command"]["steps"] for row in events
            if row.get("event") == "command" and row.get("command", {}).get("op") == "submit"
            and str(row["command"].get("id", "")).startswith("cover-")}


def uncovered(report: dict, events: list[dict]) -> list[float]:
    accepted = {row["id"]: row["accepted_ns"] for row in events if row.get("event") == "accepted"}
    terminal = {row["id"]: row for row in events if row.get("event") == "terminal"}
    gaps = []
    for decision in report["decisions"]:
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        cursor = start
        for identifier in decision["cover_program_ids"]:
            a = max(start, accepted[identifier]); b = min(end, terminal[identifier]["terminal_ns"])
            if a > cursor: gaps.append((a - cursor) / 1e6)
            cursor = max(cursor, b)
            assert terminal[identifier]["release"]["verified"]
            assert not terminal[identifier]["release"]["keys_down"]
        if cursor < end: gaps.append((end - cursor) / 1e6)
    return gaps


def usage(report: dict) -> dict:
    keys = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
    values = {key: sum(row["usage"][key] for row in report["decisions"]) for key in keys}
    values["uncached_input_tokens"] = values["input_tokens"] - values["cached_input_tokens"]
    return values


def validate_linkage(report: dict) -> None:
    default = [{"action": "coast", "extent": "long"}]
    for index, decision in enumerate(report["decisions"]):
        if index == 0:
            assert decision["cover_policy"] == default
            assert decision["cover_policy_source_iteration"] is None
        else:
            assert decision["cover_policy"] == report["decisions"][index - 1]["action"]["next_cover"]
            assert decision["cover_policy_source_iteration"] == index - 1


def main() -> None:
    defect, env_a, events_a = load("compiler-defect")
    corrected, env_b, events_b = load("corrected")
    fixed = ("vizdoom", "mode", "ticrate", "seed", "map", "skill", "iwad_sha256")
    assert {key: env_a[key] for key in fixed} == {key: env_b[key] for key in fixed}
    initial_mae = normalized_mae(descriptor(ROOT / "compiler-defect/frames/00.png"),
                                 descriptor(ROOT / "corrected/frames/00.png"))
    assert initial_mae <= 0.015
    for report in (defect, corrected):
        assert report["model"] == "gpt-6-astra" and report["effort"] == "low"
        assert report["iterations"] == 4 and report["model_authored_cover_policies"] == 4
        assert not report["score"]["map_exit"] and not report["score"]["player_dead"]
        validate_linkage(report)
    defect_submits = cover_submits(events_a)
    corrected_submits = cover_submits(events_b)
    threat = defect["decisions"][2]["action"]["next_cover"]
    assert threat == [{"action": "strafe_left", "extent": "short"},
                      {"action": "fire", "extent": "short"},
                      {"action": "strafe_right", "extent": "short"}]
    assert defect["decisions"][3]["cover_policy"] == threat
    defect_threat_steps = defect_submits["cover-3"]
    defect_duration = sum(row["duration_ms"] for row in defect_threat_steps)
    assert len(defect_threat_steps) == 16 and defect_duration == 9640
    assert defect_threat_steps[-1]["op"] == "hold"
    assert all(sum(row["duration_ms"] for row in steps) == 10000
               for steps in corrected_submits.values())
    assert all(len(steps) <= 16 and steps[-1]["op"] == "coast"
               for steps in corrected_submits.values())
    assert corrected["cover_renewals"] == 2
    corrected_gaps = uncovered(corrected, events_b)
    assert max(corrected_gaps) < 22
    baseline = json.loads((HERE / "results/map01-cover-renewal-v1/report.json").read_text())
    baseline_usage = usage(baseline); corrected_usage = usage(corrected)
    result = {
        "status": "passed",
        "scope": "two sequential four-decision same-seed development probes; model outputs are nondeterministic",
        "initial_descriptor_normalized_mae": initial_mae,
        "compiler_defect": {
            "model_authored_policies": defect["model_authored_cover_policies"],
            "visible_threat_policy_authored_and_used_next_iteration": True,
            "threat_policy_compiled_steps": len(defect_threat_steps),
            "threat_policy_compiled_duration_ms": defect_duration,
            "ends_with_hold": True,
        },
        "corrected": {
            "model_authored_policies": corrected["model_authored_cover_policies"],
            "cover_programs": corrected["cover_programs"],
            "cover_renewals": corrected["cover_renewals"],
            "all_programs_exactly_10000_ms_and_complete_cycles": True,
            "uncovered_model_segments_ms": corrected_gaps,
            "max_uncovered_model_ms": max(corrected_gaps),
            "usage": corrected_usage,
            "score": {key: corrected["score"][key] for key in
                      ("map_exit", "player_dead", "death_count", "kill_count")},
        },
        "same_seed_descriptive_usage": {
            "renewal_only_input_tokens": baseline_usage["input_tokens"],
            "cover_policy_input_tokens": corrected_usage["input_tokens"],
            "input_token_delta": corrected_usage["input_tokens"] - baseline_usage["input_tokens"],
            "input_token_delta_percent": (corrected_usage["input_tokens"] /
                                          baseline_usage["input_tokens"] - 1) * 100,
            "allocation_limit": "sequential single samples with different model outputs; no causal token claim",
        },
        "decision": "retain corrected compiler and planner/runtime policy handoff; threat-policy execution needs a new run before gameplay interpretation",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
