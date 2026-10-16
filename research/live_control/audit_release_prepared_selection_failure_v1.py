"""Independent cross-platform audit of retained prepared-selection failure."""
import hashlib
import json
from pathlib import Path

from inkscape_red_target_planner_v1 import prepare
from inkscape_selection_scorer_v1 import score

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
ROOT = HERE / "results/release-prepared-selection-live-01"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    retention, failure = read(ROOT / "retention.json"), read(ROOT / "failure.json")
    plan, report, events = (read(ROOT / "preregistration.json"),
                            read(ROOT / "report.json"), read(ROOT / "events.json"))
    candidate = prepare(ROOT / "001.png", plan["planner_roi"])
    error = None
    try: score(candidate, ROOT / "004.png")
    except ValueError as exc: error = str(exc)
    selection = [row for row in events if row.get("id") == "prepared-red-selection-01"]
    terminal = next(row for row in selection if row.get("event") == "terminal")
    checks = {
        "manifest": all(sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_failure": retention["decision"] == "RETAIN_FIRST_FAILURE_NO_RETRY" and
                         failure["allocation_passed"] is False,
        "incomplete_report": "passed" not in report and not (ROOT / "audit.json").exists(),
        "strict_scorer_failure": error == "red target must be one solid rectangle" and
            failure["runner_error"] == {"type": "ValueError", "detail": error},
        "precondition_already_selected": failure["visual_posthoc"]["pre_admission_dark_sides"] ==
            {"left": 197, "right": 197, "top": 67, "bottom": 67},
        "candidate_click_then_cleanup_cancel":
            any(row.get("event") == "step_completed" and row.get("step") == 0
                for row in selection) and terminal["status"] == "cancelled" and
            terminal["steps_completed"] == 1 and terminal["release"]["verified"] is True,
        "zero_retry_model": failure["retry_count"] == failure["model_calls"] == 0,
    }
    audit = {"passed": all(checks.values()), "checks": checks,
        "allocation_passed": False, "failure_class": failure["failure_class"],
        "files_in_manifest": len(retention["manifest"]),
        "bytes_before_receipt": retention["bytes"],
        "next_condition": failure["next_condition"]}
    (ROOT / "retained-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
