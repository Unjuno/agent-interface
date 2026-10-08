"""Describe typed-health trajectories during coast-only MAP01 model waits."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
ROOT = DOOM / "results"
RUNS = (
    "map01-v38-integrated-threat-live-01",
    "map01-v39-coast-liveness-live-01",
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(name):
    base = ROOT / name
    report_path = base / "report.json"
    events_path = base / "runtime/events.jsonl"
    report = load(report_path)
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    submitted = {row["command"]["id"]: row["command"] for row in events
                 if row.get("event") == "command" and row.get("command", {}).get("op") == "submit"}
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminals = {row["id"]: row for row in events if row.get("event") == "terminal"}
    typed = [row for row in events if row.get("event") == "typed_observation"]
    rows = []
    for decision in report["decisions"]:
        start, end = decision["controller_model_started_ns"], decision["controller_model_ended_ns"]
        source = decision["cover_validity_admission"]["source_signal"]["value"]
        intervals = []
        for ident in decision["cover_program_ids"]:
            command = submitted[ident]
            assert command["op"] == "submit" and ident in accepted and ident in terminals
            coast_only = all(step["op"] == "coast" for step in command["steps"])
            a, b = accepted[ident]["accepted_ns"], terminals[ident]["terminal_ns"]
            lo, hi = max(a, start), min(b, end)
            if lo < hi:
                intervals.append((lo, hi, ident, coast_only))
        intervals.sort()
        covered = sum(b - a for a, b, _, _ in intervals)
        coast_covered = sum(b - a for a, b, _, coast_only in intervals if coast_only)
        wait = end - start
        assert covered <= wait
        samples = [{"sequence": decision["cover_validity_admission"]["source_signal"]["sequence"],
                    "capture_ns": start, "value": source, "is_source": True}]
        for event in typed:
            if not start <= event["capture_ns"] <= end:
                continue
            health = event["signals"]["health"]
            if health["status"] != "observed":
                continue
            samples.append({"sequence": event["sequence"], "capture_ns": event["capture_ns"],
                            "value": health["value"], "is_source": False})
        samples.sort(key=lambda item: (item["capture_ns"], item["sequence"]))
        first_drop = next((item for item in samples if not item["is_source"] and item["value"] < source), None)
        minimum = min(item["value"] for item in samples)
        coast_only_wait = covered == wait and coast_covered == wait
        rows.append({
            "iteration": decision["iteration"],
            "wait_ms": round(wait / 1e6, 3),
            "coast_cover_ms": round(coast_covered / 1e6, 3),
            "coast_cover_program_ids": [ident for _, _, ident, pure in intervals if pure],
            "coast_only_wait": coast_only_wait,
            "overlapping_program_kinds": ["coast" if pure else "contains_hold" for _, _, _, pure in intervals],
            "source_health": source,
            "typed_health_samples": len(samples),
            "first_observed_drop_offset_ms": (round((first_drop["capture_ns"] - start) / 1e6, 3)
                                               if first_drop else None),
            "first_observed_drop_health": first_drop["value"] if first_drop else None,
            "last_observed_health": samples[-1]["value"],
            "minimum_observed_health": minimum,
            "observed_loss_to_minimum": source - minimum,
            "minimum_sample_sequence": min(samples, key=lambda item: item["value"])["sequence"],
            "scope": "typed observation; not physical damage attribution or counterfactual outcome",
        })
    return {"run": name,
            "sources": {"report.json": digest(report_path), "runtime/events.jsonl": digest(events_path)},
            "decisions": rows}


def main():
    runs = [analyze(name) for name in RUNS]
    coast = [row for run in runs for row in run["decisions"] if row["coast_only_wait"]]
    declines = [row for row in coast if row["observed_loss_to_minimum"] > 0]
    result = {
        "schema": "map01-coast-liveness-trajectory-audit-v1",
        "status": "PASS_SCOPED" if declines else "NO_DECLINE_OBSERVED",
        "candidate_runs": 1,
        "auditor_runs": 1,
        "retries": 0,
        "summary": {"retained_runs": len(runs), "coast_wait_decisions": len(coast),
                    "coast_waits_with_observed_health_decline": len(declines),
                    "observed_decline_decisions": [row["iteration"] for row in declines]},
        "runs": runs,
        "decision": "PASS_SCOPED establishes only that retained typed-health samples declined during some coast-only model waits. It does not show coast caused the loss or that another policy would improve the outcome.",
    }
    output = HERE / "result.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "summary": result["summary"],
                      "output": output.name}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
