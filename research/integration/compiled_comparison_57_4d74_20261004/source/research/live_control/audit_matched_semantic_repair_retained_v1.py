"""Audit the retained first matched semantic-repair capacity failure."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/matched-semantic-repair-live-01"
PLAN = HERE / "matched_semantic_repair_live_v1_prereg.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(PLAN)
    failure = read(ROOT / "failure.json")
    retention = read(ROOT / "retention.json")
    arm = ROOT / "arm-01-local"
    events = read(arm / "events.json")
    owner = read(arm / "owner-events.json")
    process = read(arm / "initial-model/process.json")
    model_events = [json.loads(line) for line in
                    (arm / "initial-model/events.jsonl").read_text(encoding="utf-8").splitlines()]
    terminals = [row for row in events if row.get("event") == "terminal"]
    observations = [row for row in events if row.get("event") == "observation"]
    checks = {
        "manifest": all((ROOT / name).is_file() and sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all((REPO / name).is_file() and sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_outcome": retention["decision"] == "RETAIN_FIRST_OUTCOME_FAILED_NO_RETRY"
            and failure["retry_count"] == 0,
        "typed_failure": failure["failure_class"] == "upstream_model_capacity_before_completed_turn"
            and process["exit_code"] == 1 and process["observed_model_identity"] is None,
        "capacity_evidence": [row["type"] for row in model_events] ==
            ["thread.started", "turn.started", "error", "turn.failed"]
            and all("at capacity" in row.get("message", row.get("error", {}).get("message", ""))
                    for row in model_events[2:]),
        "no_completed_model_turn": not any(row["type"] == "turn.completed" for row in model_events)
            and not any(row["type"] == "item.completed" for row in model_events),
        "preflight_cache_only": read(ROOT / "preflight/gate-report.json")["accepted"] is True
            and read(ROOT / "preflight/gate-report.json")["model_calls"] == 0,
        "gui_prefix_only": len(terminals) == 2
            and [row["id"] for row in terminals] == ["matched-repair-nav-1", "matched-repair-fill-1"]
            and not any(row.get("event") in ("test_surface_resized", "semantic_probe") for row in events),
        "exact_source": observations[-1]["id"] == "matched-repair-source"
            and observations[-1]["exact"] is True
            and observations[-1]["pointer_binding"]["geometry"] == plan["expected_source_geometry"],
        "empty_release": all(row["status"] == "completed" and row["release"]["verified"] is True
            and row["release"]["keys_down"] == [] and row["release"]["buttons_down"] == []
            for row in terminals)
            and owner[-1]["reason"] == "close" and owner[-1]["verified"] is True
            and owner[-1]["keys_down"] == [] and owner[-1]["buttons_down"] == [],
        "comparison_unobserved": failure["comparison_metrics"] is None,
    }
    result = {"passed": all(checks.values()), "checks": checks,
              "allocation_passed": False, "failure_class": failure["failure_class"],
              "model_threads_started": 1, "completed_model_turns": 0,
              "files_in_manifest": len(retention["manifest"]),
              "bytes_before_receipt": retention["bytes"], "scope": failure["scope"]}
    (ROOT / "retained-audit.json").write_text(json.dumps(result, indent=2) + "\n",
                                               encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
