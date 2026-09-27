"""Audit the frozen, single-allocation Astra MAP01 attempt."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-astra-attempt-v1"
PREREG = HERE / "map01_astra_attempt_v1_prereg.json"
OUT = HERE / "results/map01-astra-attempt-v1-audit.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prereg = json.loads(PREREG.read_text())
    report = json.loads((ROOT / "report.json").read_text())
    environment = json.loads((ROOT / "environment.json").read_text())
    events = [json.loads(line) for line in (ROOT / "events.jsonl").read_text().splitlines()]
    score = report["score"]
    assert prereg["status"] == "frozen_before_first_model_call"
    for relative, expected in prereg["source_sha256"].items():
        assert sha(HERE.parents[1] / relative) == expected
    assert report["model"] == prereg["model"] == "gpt-6-astra"
    assert report["effort"] == prereg["effort"] == "low"
    assert environment["seed"] == prereg["seed"] == 990609
    assert environment["map"] == "MAP01" and environment["skill"] == 1
    assert environment["mode"] == "Mode.ASYNC_SPECTATOR" and environment["ticrate"] == 35
    assert report["iterations"] == 13 <= prereg["iterations_max"]
    assert score["episode_finished"] and score["player_dead"]
    assert score["death_count"] == 1 and score["kill_count"] == 1
    assert not score["map_exit"] and not score["one_life_map_exit"]
    clock = next(row for row in events if row["event"] == "clock_probe")
    measured_ticrate = (clock["after_tic"] - clock["before_tic"]) / clock["wall_seconds"]
    assert clock["no_advance_calls_during_wait"] and 34 <= measured_ticrate <= 36
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    cover_gaps_ms = []
    for decision in report["decisions"]:
        cover = f"cover-{decision['iteration']}"
        assert accepted[cover]["accepted_ns"] <= decision["controller_model_started_ns"]
        cover_gaps_ms.append(max(0, decision["controller_model_ended_ns"] -
                                 terminals[cover]["terminal_ns"]) / 1e6)
        assert terminals[cover]["release"]["verified"]
        assert not terminals[cover]["release"]["buttons_down"]
        assert not terminals[cover]["release"]["keys_down"]
    plan_terminals = [row for row in events if row.get("event") == "terminal"
                      and str(row.get("id", "")).startswith("plan-")]
    assert all(row["status"] == "completed" and row["release"]["verified"]
               for row in plan_terminals)
    assert report["contingencies_authored"] == 8
    assert report["contingency_branches_taken"] == 0
    assert report["program_admissions"] == 13
    assert report["extra_program_admissions_vs_one_bundle"] == 1
    final = report["decisions"][-1]
    assert final["action"]["state"] == "dead"
    assert not final["action"]["commands"] and not final["action"]["contingencies"]
    usage_keys = ("input_tokens", "cached_input_tokens", "output_tokens",
                  "reasoning_output_tokens")
    usage = {key: sum(row["usage"][key] for row in report["decisions"])
             for key in usage_keys}
    manifest = json.loads((ROOT / "frame-manifest.json").read_text())
    assert len(manifest) == report["iterations"]
    assert all(sha(ROOT / row["file"]) == row["sha256"] for row in manifest)
    video = json.loads((ROOT / "video.json").read_text())
    assert sha(ROOT / video["file"]) == video["sha256"]
    result = {
        "status": "passed",
        "disposition": "retained_failed_hero_attempt",
        "allocation_id": prereg["allocation_id"],
        "model": report["model"],
        "effort": report["effort"],
        "iterations": report["iterations"],
        "wall_seconds": score["wall_control_ns"] / 1e9,
        "model_seconds": report["model_wall_seconds"],
        "nonmodel_seconds": score["wall_control_ns"] / 1e9 - report["model_wall_seconds"],
        "measured_clock_probe_tics_per_second": measured_ticrate,
        "model_intervals_fully_covered_by_local_programs":
            sum(gap == 0 for gap in cover_gaps_ms),
        "model_intervals_with_uncovered_tail": sum(gap > 0 for gap in cover_gaps_ms),
        "total_uncovered_model_tail_ms": sum(cover_gaps_ms),
        "max_uncovered_model_tail_ms": max(cover_gaps_ms),
        "score": {key: score[key] for key in ("map_exit", "episode_finished",
                                                "player_dead", "death_count",
                                                "kill_count", "one_life_map_exit")},
        "contingencies_authored": report["contingencies_authored"],
        "contingency_branches_taken": report["contingency_branches_taken"],
        "program_admissions": report["program_admissions"],
        "extra_program_admissions_vs_one_bundle":
            report["extra_program_admissions_vs_one_bundle"],
        "effect_receipt_commands": report["effect_receipt_commands"],
        "effect_observation_samples": report["effect_observation_samples"],
        "usage": {**usage,
                  "uncached_input_tokens": usage["input_tokens"] - usage["cached_input_tokens"]},
        "video": video,
        "observed_limit": "the run entered later rooms and killed one enemy, but fixed ten-second cover expired before seven of thirteen model calls and coarse control did not recover from sustained damage",
        "claim_limit": "single frozen attempt; no clear, model comparison, reliability, or human-tempo claim",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
