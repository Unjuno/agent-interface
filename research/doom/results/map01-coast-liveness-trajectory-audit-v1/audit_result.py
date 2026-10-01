"""Independent raw-source checks for the retained coast trajectory result."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "results"
RUNS = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    result = read(HERE / "result.json")
    assert result["schema"] == "map01-coast-liveness-trajectory-audit-v1"
    assert result["candidate_runs"] == result["auditor_runs"] == 1 and result["retries"] == 0
    assert [run["run"] for run in result["runs"]] == list(RUNS)
    all_rows = []
    for run in result["runs"]:
        base = ROOT / run["run"]
        report_path, events_path = base / "report.json", base / "runtime/events.jsonl"
        assert run["sources"] == {"report.json": sha(report_path),
                                   "runtime/events.jsonl": sha(events_path)}
        report = read(report_path)
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
        typed = [e for e in events if e.get("event") == "typed_observation"]
        submitted = {e["command"]["id"]: e["command"] for e in events
                     if e.get("event") == "command" and e.get("command", {}).get("op") == "submit"}
        accepted = {e["id"]: e for e in events if e.get("event") == "accepted"}
        terminals = {e["id"]: e for e in events if e.get("event") == "terminal"}
        assert len(run["decisions"]) == len(report["decisions"]) == 6
        for row, decision in zip(run["decisions"], report["decisions"], strict=True):
            start, end = decision["controller_model_started_ns"], decision["controller_model_ended_ns"]
            source = decision["cover_validity_admission"]["source_signal"]["value"]
            health = [e["signals"]["health"]["value"] for e in typed
                      if start <= e["capture_ns"] <= end and
                      e["signals"]["health"]["status"] == "observed"]
            assert row["iteration"] == decision["iteration"]
            assert row["source_health"] == source
            assert row["minimum_observed_health"] == min([source] + health)
            assert row["observed_loss_to_minimum"] == source - min([source] + health)
            assert row["wait_ms"] == round((end - start) / 1e6, 3)
            classifications = []
            coast_ns = total_ns = 0
            for ident in decision["cover_program_ids"]:
                command = submitted[ident]
                assert ident in accepted and ident in terminals
                pure_coast = all(step["op"] == "coast" for step in command["steps"])
                lo = max(start, accepted[ident]["accepted_ns"])
                hi = min(end, terminals[ident]["terminal_ns"])
                if lo < hi:
                    total_ns += hi - lo
                    if pure_coast:
                        coast_ns += hi - lo
                        classifications.append("coast")
                    else:
                        classifications.append("contains_hold")
            assert row["overlapping_program_kinds"] == classifications
            assert row["coast_cover_ms"] == round(coast_ns / 1e6, 3)
            assert row["coast_only_wait"] == (total_ns == end - start and coast_ns == end - start)
            assert row["first_observed_drop_offset_ms"] is None or row["first_observed_drop_offset_ms"] >= 0
            all_rows.append(row)
    coast = [row for row in all_rows if row["coast_only_wait"]]
    declines = [row for row in coast if row["observed_loss_to_minimum"] > 0]
    assert result["summary"] == {"retained_runs": 2, "coast_wait_decisions": len(coast),
                                  "coast_waits_with_observed_health_decline": len(declines),
                                  "observed_decline_decisions": [row["iteration"] for row in declines]}
    assert result["status"] == ("PASS_SCOPED" if declines else "NO_DECLINE_OBSERVED")
    print(json.dumps({"auditor_passed": True, "coast_waits": len(coast),
                      "declines": len(declines), "source_hashes_verified": 4}, indent=2))


if __name__ == "__main__":
    main()
