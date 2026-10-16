"""Independent audit of pre-artifact semantic feedback integration."""
import hashlib
import json
from pathlib import Path

from executor_v11 import program_sha256
from inkscape_selection_frame_probe_v1 import reconcile_artifact
from inkscape_selection_scorer_v2 import score


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "release_prepared_selection_live_v5_prereg.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def semantic(result):
    keys = ("success", "reason", "expected_target", "observed_support",
            "edge_delta", "red_coverage_ratio", "zones", "dark_pixels",
            "target_identity_valid", "selection_handles_visible")
    return {key: result[key] for key in keys}


def main():
    plan = read(PREREG)
    root = REPO/plan["output"]
    report, events = read(root/"report.json"), read(root/"events.json")
    early = report["clients"]["early"]
    accepted = report["selection_accepted"]
    feedback = report["selection_observation"]
    useful = report["semantic_observation"]
    terminal = report["selection_terminal"]
    probes = report["semantic_scores"]
    reconciliations = report["semantic_probe_reconciliations"]
    metrics = report["metrics_ms"]
    admission_path = root/Path(report["admission_observation"]["image"]).name
    feedback_path = root/Path(feedback["image"]).name
    useful_path = root/Path(useful["image"]).name
    pre_score = score(early["candidate"], admission_path)
    first_path_score = score(early["candidate"], feedback_path)
    useful_path_score = score(early["candidate"], useful_path)
    first_reconciliation = reconcile_artifact(probes[0]["score"], feedback_path)
    useful_reconciliation = reconcile_artifact(probes[-1]["score"], useful_path)
    def matching(rows, sequence):
        return next(row for row in rows if row["sequence"] == sequence)
    observations = [row for row in events if row.get("event") == "observation" and
                    row.get("id") == accepted["id"]]
    checks = {
        "frozen_sources": all(sha(REPO/name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "allocation_all_pass": report["passed"] is True and all(report["checks"].values()),
        "prepared_lineage": (early["reconciled_state"]["state"] ==
            "PREPARED_REQUIRES_FRESH_ACTION_VALIDITY" and
            early["preparation_completed_ns"] < report["terminal"]["terminal_ns"]),
        "fresh_coherent_admission": (report["admission_validation"]["status"] ==
            "VALID_CURRENT" and report["binding_attempts"][-1]["status"] == "READY" and
            report["admission_validation_completed_ns"] <= report["selection_submit_ns"] <=
            accepted["accepted_ns"]),
        "candidate_exactly_admitted": (accepted["steps"] == 2 and
            accepted["program_sha256"] == program_sha256(report["selection_program"]) and
            len([row for row in events if row.get("event") == "accepted"]) == 2),
        "probe_registered_and_waiting": (report["probe_registration"]["status"] ==
            "REGISTERED_NO_AUTHORITY" and report["semantic_request_registered_ns"] <=
            report["selection_submit_ns"]),
        "first_boundary_is_observation": (report["selection_boundary"]["status"] ==
            "FEEDBACK" and report["selection_boundary"]["record"] == feedback),
        "false_then_true_semantics": (len(probes) == 2 and
            probes[0]["score"]["success"] is False and probes[1]["score"]["success"] is True and
            semantic(probes[0]["score"]) == semantic(first_path_score) and
            semantic(probes[1]["score"]) == semantic(useful_path_score) and
            pre_score["success"] is False and useful["sequence"] > feedback["sequence"]),
        "probe_before_artifact": all(
            probe["probe_completed_ns"] < matching(reconciliations, probe["sequence"])
                ["image_ready_ns"] and
            probe["runtime_emit_ns"] < matching(reconciliations, probe["sequence"])
                ["runtime_emit_ns"] <= matching(observations, probe["sequence"])["runtime_emit_ns"]
            for probe in probes),
        "exact_artifact_reconciliation": (first_reconciliation["matches"] is True and
            useful_reconciliation["matches"] is True and
            first_reconciliation == reconciliations[0]["reconciliation"] and
            useful_reconciliation == reconciliations[1]["reconciliation"]),
        "client_received_ordered_probes": ([row["reply"]["records"][-1]
            for row in report["semantic_client"]["exchanges"]] == probes and
            report["semantic_feedback_received_ns"] ==
            report["semantic_client"]["exchanges"][-1]["client_returned_ns"]),
        "terminal_verified_release": (terminal["status"] == "completed" and
            terminal["steps_completed"] == 2 and terminal["release"]["verified"] is True and
            terminal["release"]["keys_down"] == [] and
            terminal["release"]["buttons_down"] == []),
        "timing_limits": (metrics["focus_to_semantic_score_ms"] <=
            plan["thresholds_ms"]["focus_to_semantic_score_lte"] and
            metrics["selection_admission_to_first_feedback_received_ms"] <=
            plan["thresholds_ms"]["admission_to_first_feedback_lte"] and
            metrics["selection_admission_to_semantic_score_ms"] <=
            plan["thresholds_ms"]["admission_to_semantic_score_lte"] and
            metrics["selection_admission_to_semantic_feedback_received_ms"] <=
            plan["thresholds_ms"]["admission_to_semantic_client_lte"] and
            max(metrics["first_probe_compute_ms"], metrics["useful_probe_compute_ms"]) <=
            plan["thresholds_ms"]["probe_compute_lte"]),
        "zero_model_retry_cancel": (report["model_calls"] == report["retry_count"] == 0 and
            not any(row.get("event") == "cancel_requested" for row in events)),
    }
    audit = {"passed": all(checks.values()), "checks": checks,
             "metrics_ms": metrics, "candidate": early["candidate"],
             "first_probe": probes[0], "useful_probe": probes[-1],
             "events": len(events), "scope": plan["scope"]}
    (root/"audit.json").write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
