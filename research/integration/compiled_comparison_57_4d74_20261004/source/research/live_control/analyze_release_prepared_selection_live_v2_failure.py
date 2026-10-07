"""Classify the first neutral-fault prepared-selection failure."""
import hashlib
import json
from pathlib import Path

from inkscape_red_target_planner_v1 import prepare, validate
from inkscape_selection_scorer_v2 import score

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
ROOT = REPO / "results-local/live_control/release-prepared-selection-live-02"
PREREG = HERE / "release_prepared_selection_live_v2_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan, report, events = read(PREREG), read(ROOT / "report.json"), read(ROOT / "events.json")
    candidate = prepare(ROOT / "001.png", plan["planner_roi"])
    fresh = validate(candidate, ROOT / "003.png"); pre_score = score(candidate, ROOT / "003.png")
    observation = next(row for row in events if row.get("id") == "prepared-pre-admission")
    selection = [row for row in events if row.get("id") == "prepared-red-selection-02"]
    terminal = next(row for row in selection if row.get("event") == "terminal")
    failure = {"allocation_passed": False,
        "failure_class": "restored_focus_binding_not_coherent_before_admission",
        "frozen_sources_match": all(sha(REPO / name) == digest
                                    for name, digest in plan["source_sha256"].items()),
        "runner_error": {"type": "RuntimeError", "detail": "selection feedback missing"},
        "report_incomplete": "passed" not in report,
        "neutral_precondition": {"fault_point": plan["point"],
            "outside_target": not (candidate["target"]["bbox"][0] <= plan["point"]["x"] <
                candidate["target"]["bbox"][2] and candidate["target"]["bbox"][1] <=
                plan["point"]["y"] < candidate["target"]["bbox"][3]),
            "fresh_target_validation": fresh, "pre_selection_score": pre_score},
        "binding_fault": {"pointer_binding": observation["pointer_binding"],
            "before": observation["pointer_context_before"],
            "after": observation["pointer_context_after"]},
        "safe_refusal": {"accepted": len([row for row in selection
            if row.get("event") == "accepted"]),
            "pointer_admissions": len([row for row in selection
                if row.get("event") == "pointer_admission"]), "terminal": terminal},
        "wait_defect": "client waited only for observation and missed an already-emitted terminal, then timed out at3s",
        "next_condition": "require coherent non-null pointer binding before acceptance; wait for observation|terminal first boundary; keep neutral fault and scorer v2",
        "retry_count": 0, "model_calls": 0}
    (ROOT / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
    print(json.dumps(failure, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
