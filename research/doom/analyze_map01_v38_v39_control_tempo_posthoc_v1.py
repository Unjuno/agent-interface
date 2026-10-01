"""Hash-anchored posthoc control-tempo reconstruction from retained live logs."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE / "results"
OUT = ROOT / "map01-v38-v39-control-tempo-posthoc-v1"
RUNS = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ms(ns):
    return round(ns / 1e6, 3)


def overlap(start, end, other_start, other_end):
    return max(0, min(end, other_end) - max(start, other_start))


def analyze_run(name):
    root = ROOT / name
    report_path, event_path = root / "report.json", root / "runtime/events.jsonl"
    report = read(report_path)
    events = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    submitted = {row["command"]["id"]: row["command"] for row in events
                 if row.get("event") == "command" and
                 row.get("command", {}).get("op") == "submit"}
    typed = [row for row in events if row.get("event") == "typed_observation"]
    observations = [row for row in events if row.get("event") == "observation"]
    assert set(accepted) == set(terminals) == set(submitted)
    assert report["iterations"] == len(report["decisions"]) == 6
    assert report["score"] == next(row for row in events if row.get("event") == "post_control_score")
    assert all(row["release"]["verified"] and row["release"]["keys_down"] == [] and
               row["release"]["buttons_down"] == [] for row in terminals.values())
    rows = []
    for decision in report["decisions"]:
        index = decision["iteration"]
        start, end = decision["controller_model_started_ns"], decision["controller_model_ended_ns"]
        assert start < end
        cover_intervals = []
        for identifier in decision["cover_program_ids"]:
            command = submitted[identifier]
            a, b = accepted[identifier]["accepted_ns"], terminals[identifier]["terminal_ns"]
            assert a <= b
            motor = any(step["op"] == "hold" and step.get("keys") for step in command["steps"])
            clipped_start, clipped_end = max(start, a), min(end, b)
            if clipped_start < clipped_end:
                cover_intervals.append((clipped_start, clipped_end, bool(motor), identifier))
        cover_intervals.sort()
        assert all(first[1] <= second[0] for first, second in zip(
            cover_intervals, cover_intervals[1:])), "cover envelopes overlap"
        motor_ns = sum(b - a for a, b, motor, _ in cover_intervals if motor)
        coast_ns = sum(b - a for a, b, motor, _ in cover_intervals if not motor)
        uncovered_ns = end - start - motor_ns - coast_ns
        assert uncovered_ns >= 0
        source_health = decision["cover_validity_admission"]["source_signal"]["value"]
        health_samples = [row["signals"]["health"]["value"] for row in typed
                          if start <= row["capture_ns"] <= end and
                          row["signals"]["health"]["status"] == "observed"]
        min_health = min([source_health] + health_samples) if typed else None
        rows.append({"iteration": index, "planner_status": decision["planner_turn_status"],
                     "answer_eligible": decision["planner_answer_eligible"],
                     "final_admission": decision["final_action_admission"]["status"],
                     "cover_source_iteration": decision.get("cover_policy_source_iteration"),
                     "cover_policy_authored": decision["cover_validity_admission"]["authored"] is not None,
                     "model_wait_ms": ms(end - start),
                     "motor_capable_cover_envelope_ms": ms(motor_ns),
                     "coast_cover_envelope_ms": ms(coast_ns),
                     "no_cover_program_envelope_ms": ms(uncovered_ns),
                     "health_at_cover_source": source_health,
                     "minimum_typed_health_during_wait": min_health,
                     "observed_health_loss_during_wait":
                         (source_health - min_health if min_health is not None else None),
                     "typed_health_samples": len(health_samples),
                     "cover_ids": decision["cover_program_ids"]})
    first_exact = []
    for identifier, admission in accepted.items():
        if not identifier.startswith("plan-") or "refresh" in identifier:
            continue
        program_samples = [row for row in observations if row.get("id") == identifier]
        if not program_samples:
            first_exact.append({"id": identifier, "first_exact_capture_ms": None,
                                "first_exact_artifact_ms": None})
            continue
        sample = min(program_samples, key=lambda row: row["capture_ns"])
        first_exact.append({"id": identifier,
                            "first_exact_capture_ms": ms(sample["capture_ns"] - admission["accepted_ns"]),
                            "first_exact_artifact_ms": ms(sample["artifact_ready_ns"] - admission["accepted_ns"]),
                            "semantic_task_feedback": "unverified"})
    release_rows = []
    for release in (row for row in events if row.get("event") == "input_released"):
        identifier = release["id"]
        matching = [decision for decision in report["decisions"]
                    if decision.get("running_action_invalidation") is not None and
                    any(binding["submit"]["command"]["id"] == identifier
                        for binding in decision["running_action_guard"]["program_bindings"])]
        assert len(matching) == 1
        snapshot = matching[0]["running_action_invalidation"]["result"]["snapshot"]
        source = next(row for row in typed if row["sequence"] == snapshot["sequence"])
        verified = release["owner_release"]["verified_ns"]
        assert verified <= terminals[identifier]["terminal_ns"]
        release_rows.append({"id": identifier,
                             "evidence_sequence": snapshot["sequence"],
                             "health_at_revocation": snapshot["signals"]["health"]["value"],
                             "capture_to_verified_physical_release_ms": ms(verified - source["capture_ns"]),
                             "typed_emit_to_verified_physical_release_ms": ms(verified - source["emit_ns"]),
                             "verified_physical_release_to_terminal_ms": ms(
                                 terminals[identifier]["terminal_ns"] - verified)})
    totals = {"model_wait_ms": round(sum(row["model_wait_ms"] for row in rows), 3),
              "motor_capable_cover_envelope_ms": round(sum(row["motor_capable_cover_envelope_ms"] for row in rows), 3),
              "coast_cover_envelope_ms": round(sum(row["coast_cover_envelope_ms"] for row in rows), 3),
              "no_cover_program_envelope_ms": round(sum(row["no_cover_program_envelope_ms"] for row in rows), 3),
              "completed_answers": sum(row["planner_status"] == "completed" for row in rows),
              "plan_admissions": report["program_admissions"],
              "early_physical_releases": len(release_rows),
              "independent_kills": report["score"]["kill_count"],
              "independent_deaths": report["score"]["death_count"],
              "independent_map_exit": report["score"]["map_exit"]}
    assert abs(totals["model_wait_ms"] - sum(totals[key] for key in (
        "motor_capable_cover_envelope_ms", "coast_cover_envelope_ms",
        "no_cover_program_envelope_ms"))) < .02
    return {"run": name, "source_sha256": {"report.json": sha(report_path),
           "runtime/events.jsonl": sha(event_path)}, "decisions": rows,
           "totals": totals, "first_exact_plan_feedback": first_exact,
           "running_release_latency": release_rows,
           "scope": "posthoc program-envelope occupancy, not measured physical key-down duration or verified task-useful feedback"}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    runs = [analyze_run(name) for name in RUNS]
    value = {"schema": "map01-v38-v39-control-tempo-posthoc-v1", "analysis_kind": "descriptive posthoc",
             "runs": runs,
             "limits": "same fixture/seed/model but stochastic gameplay and different model actions; no causal speed, survival, useful-feedback or human-tempo comparison"}
    OUT.mkdir()
    (OUT / "analysis.json").write_text(json.dumps(value, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
    print(json.dumps({row["run"]: row["totals"] for row in runs}, indent=2))


if __name__ == "__main__":
    main()
