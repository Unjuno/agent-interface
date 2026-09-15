"""Independent audit of executed release-prepared Inkscape selection."""
import hashlib
import json
from pathlib import Path

from inkscape_selection_scorer_v2 import score

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
PREREG = HERE / "release_prepared_selection_live_v2_prereg.json"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan = read(PREREG); root = REPO / plan["output"]
    report, events = read(root / "report.json"), read(root / "events.json")
    early = report["clients"]["early"]; accepted = report["selection_accepted"]
    feedback = report["selection_observation"]; terminal = report["selection_terminal"]
    metrics = report["metrics_ms"]
    pre_score = score(early["candidate"], root / "003.png")
    post_score = score(early["candidate"], root / Path(feedback["image"]).name)
    checks = {
        "frozen_sources": all(sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "allocation_all_pass": report["passed"] is True and all(report["checks"].values()),
        "prepared_lineage": early["reconciled_state"]["state"] ==
            "PREPARED_REQUIRES_FRESH_ACTION_VALIDITY" and
            early["preparation_completed_ns"] < report["terminal"]["terminal_ns"],
        "fresh_validation_before_admission": report["admission_validation"]["status"] ==
            "VALID_CURRENT" and report["admission_validation_completed_ns"] <=
            report["selection_submit_ns"] <= accepted["accepted_ns"],
        "candidate_exactly_admitted": accepted["event"] == "accepted" and
            accepted["steps"] == [early["candidate"]["action"], {"op": "observe"}] and
            len([row for row in events if row.get("event") == "accepted"]) == 2,
        "independent_visible_effect": pre_score == report["pre_selection_score"] and
            pre_score["success"] is False and post_score == report["semantic_score"] and
            post_score["success"] is True,
        "feedback_precedes_score": feedback["capture_ns"] >= accepted["accepted_ns"] and
            report["first_feedback_received_ns"] >= feedback["capture_ns"] and
            report["semantic_score_completed_ns"] >= report["first_feedback_received_ns"],
        "terminal_verified_release": terminal["status"] == "completed" and
            terminal["steps_completed"] == 2 and terminal["release"]["verified"] is True and
            terminal["release"]["keys_down"] == [] and terminal["release"]["buttons_down"] == [],
        "timing_limits": metrics["focus_to_semantic_score_ms"] <=
            plan["thresholds_ms"]["focus_to_semantic_score_lte"] and
            metrics["selection_admission_to_first_feedback_received_ms"] <=
            plan["thresholds_ms"]["admission_to_first_feedback_lte"] and
            metrics["selection_admission_to_semantic_score_ms"] <=
            plan["thresholds_ms"]["admission_to_semantic_score_lte"],
        "zero_model_retry_cancel": report["model_calls"] == report["retry_count"] == 0 and
            not any(row.get("event") == "cancel_requested" for row in events),
    }
    audit = {"passed": all(checks.values()), "checks": checks,
        "metrics_ms": metrics, "candidate": early["candidate"],
        "semantic_score": post_score, "events": len(events), "scope": plan["scope"]}
    (root / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2)); return 0 if audit["passed"] else 1

if __name__ == "__main__": raise SystemExit(main())
