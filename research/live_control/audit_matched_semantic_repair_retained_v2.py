"""Audit retained matched semantic-repair v2 freshness failure evidence."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/matched-semantic-repair-live-02"
PLAN = HERE / "matched_semantic_repair_live_v2_prereg.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, failure = read(PLAN), read(ROOT / "failure.json")
    retention, diagnosis = read(ROOT / "retention.json"), read(ROOT / "diagnosis.json")
    local = read(ROOT / "arm-01-local/report.json")
    model = read(ROOT / "arm-02-model/report.json")
    model_events = read(ROOT / "arm-02-model/events.json")
    owner = read(ROOT / "arm-02-model/owner-events.json")
    terminals = [row for row in model_events if row.get("event") == "terminal"]
    records = local["model_records"] + [model["initial_outcome"]["result"],
                                        model["reacquisition_outcome"]["result"]]
    checks = {
        "manifest": all((ROOT / name).is_file() and sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all((REPO / name).is_file() and sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_outcome": retention["decision"] == "RETAIN_FIRST_OUTCOME_FAILED_NO_RETRY"
            and failure["retry_count"] == 0,
        "failure_class": failure["failure_class"] ==
            "model_reacquisition_outlived_source_observation_freshness",
        "diagnosis": diagnosis["passed"] is True and all(diagnosis["checks"].values())
            and diagnosis["delayed_resolution"]["status"] == "STALE"
            and diagnosis["fresh_control_resolution"]["eligible"] is True,
        "local_arm_completed": local["status"] == "COMPLETED" and local["passed"] is True
            and all(local["checks"].values()) and local["actual"] == {"value": ["t000214"]},
        "model_arm_stopped": model["status"] == "STARTED"
            and model["initial_outcome"]["status"] == "COMPLETED"
            and model["reacquisition_outcome"]["status"] == "COMPLETED"
            and not any(row.get("id", "").startswith("matched-repair-submit-2")
                        for row in model_events),
        "model_accounting": len(records) == len({row["call_id"] for row in records}) == 3
            and sum(row["usage"]["input_tokens"] for row in records) == 28053,
        "model_point_correct_but_stale": model["reacquisition_outcome"]["result"]
            ["grounding"]["submit_point"] == [270, 243]
            and model["reacquisition_outcome"]["caller_elapsed_ms"] > 3000,
        "safe_prefix_release": [row["id"] for row in terminals] ==
            ["matched-repair-nav-2", "matched-repair-fill-2"]
            and all(row["status"] == "completed" and row["release"]["verified"] is True
                    and row["release"]["keys_down"] == []
                    and row["release"]["buttons_down"] == [] for row in terminals)
            and owner[-1]["reason"] == "close" and owner[-1]["verified"] is True
            and owner[-1]["keys_down"] == [] and owner[-1]["buttons_down"] == [],
        "comparison_unobserved": failure["comparison_metrics"] is None
            and not (ROOT / "report.json").exists(),
    }
    result = {"passed": all(checks.values()), "checks": checks,
        "allocation_passed": False, "failure_class": failure["failure_class"],
        "completed_arms": 1, "started_arms": 2, "successful_model_calls": 3,
        "input_tokens": 28053, "files_in_manifest": len(retention["manifest"]),
        "bytes_before_receipt": retention["bytes"], "scope": failure["scope"]}
    (ROOT / "retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
        encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
