"""Audit bounded cover renewal while a frontier model call is pending."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / "results/map01-cover-renewal-v1"
OUT = HERE / "results/map01-cover-renewal-v1-audit.json"


def main() -> None:
    report = json.loads((ROOT / "report.json").read_text())
    environment = json.loads((ROOT / "environment.json").read_text())
    events = [json.loads(line) for line in (ROOT / "events.jsonl").read_text().splitlines()]
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    assert report["model"] == "gpt-6-astra" and report["effort"] == "low"
    assert report["iterations"] == 4 and environment["mode"] == "Mode.ASYNC_SPECTATOR"
    assert report["cover_programs"] == 6 and report["cover_renewals"] == 2
    assert len(report["cover_renewal_gaps_ms"]) == 2
    uncovered_by_decision = []
    all_release_verified = True
    for decision in report["decisions"]:
        start = decision["controller_model_started_ns"]
        end = decision["controller_model_ended_ns"]
        intervals = []
        for identifier in decision["cover_program_ids"]:
            a = accepted[identifier]["accepted_ns"]
            terminal = terminals[identifier]
            b = terminal["terminal_ns"]
            intervals.append((max(start, a), min(end, b)))
            all_release_verified &= terminal["release"]["verified"]
            all_release_verified &= not terminal["release"]["buttons_down"]
            all_release_verified &= not terminal["release"]["keys_down"]
        cursor = start
        gaps = []
        for a, b in sorted(intervals):
            if a > cursor:
                gaps.append((a - cursor) / 1e6)
            cursor = max(cursor, b)
        if cursor < end:
            gaps.append((end - cursor) / 1e6)
        uncovered_by_decision.append(gaps)
    uncovered = [gap for gaps in uncovered_by_decision for gap in gaps]
    assert all_release_verified
    assert max(uncovered) < 22
    score = report["score"]
    assert not score["map_exit"] and not score["player_dead"]
    result = {
        "status": "passed",
        "scope": "four-decision development probe, not a frozen hero attempt",
        "iterations": report["iterations"],
        "model_seconds": report["model_wall_seconds"],
        "wall_seconds": score["wall_control_ns"] / 1e9,
        "cover_programs": report["cover_programs"],
        "cover_renewals": report["cover_renewals"],
        "recorded_terminal_to_next_admission_ms": report["cover_renewal_gaps_ms"],
        "uncovered_model_segments_ms": uncovered,
        "total_uncovered_model_ms": sum(uncovered),
        "max_uncovered_model_ms": max(uncovered),
        "all_cover_terminals_released": all_release_verified,
        "score": {key: score[key] for key in ("map_exit", "episode_finished",
                                                "player_dead", "death_count",
                                                "kill_count")},
        "observed_result": "two expired ten-second cover programs were renewed from fresh sequence evidence while their model calls remained pending",
        "decision": "retain renewal as a shared lifetime mechanism; a small release-to-readmit gap remains and gameplay benefit is unproven",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
