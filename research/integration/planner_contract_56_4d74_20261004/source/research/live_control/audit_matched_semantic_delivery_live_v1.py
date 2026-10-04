"""Independent audit of matched path versus frame semantic delivery."""
import hashlib
import json
from pathlib import Path
import statistics

from executor_v11 import program_sha256
from inkscape_selection_frame_probe_v1 import reconcile_artifact
from inkscape_selection_scorer_v2 import score


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PREREG = HERE / "matched_semantic_delivery_live_v1_prereg.json"


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
    report = read(root/"report.json")
    arm_checks = []
    samples = {"path": [], "frame": []}
    candidates = []
    programs = []
    for ordinal, embedded in enumerate(report["arms"]):
        mode = plan["order"][ordinal]
        arm_root = root/f"arm-{ordinal+1:02d}-{mode}"
        arm = read(arm_root/"report.json")
        events = read(arm_root/"events.json")
        feedback = arm["client"]["feedback"]
        first_observation = next(row for row in arm["observations"]
            if row["sequence"] == feedback[0]["boundary"]["sequence"])
        useful_observation = arm["useful_observation"]
        first_path = arm_root/Path(first_observation["image"]).name
        useful_path = arm_root/Path(useful_observation["image"]).name
        first_score = score(arm["candidate"], first_path)
        useful_score = score(arm["candidate"], useful_path)
        checks = {
            "embedded_exact": embedded == arm,
            "mode_seed": arm["mode"] == mode and arm["seed"] == plan["seed"],
            "program": arm["accepted"]["program_sha256"] == program_sha256(arm["program"]),
            "false_true": first_score["success"] is False and useful_score["success"] is True and
                semantic(first_score) == semantic(feedback[0]["score"]) and
                semantic(useful_score) == semantic(feedback[1]["score"]),
            "release": arm["terminal"]["status"] == "completed" and
                arm["terminal"]["steps_completed"] == 2 and
                arm["terminal"]["release"]["verified"] is True and
                arm["terminal"]["release"]["keys_down"] == [] and
                arm["terminal"]["release"]["buttons_down"] == [],
            "client_order": arm["client_registered_ns"] <= arm["submit_ns"] <=
                arm["accepted"]["accepted_ns"] and len(feedback) == 2,
        }
        if mode == "frame":
            first_receipt = reconcile_artifact(feedback[0]["score"], first_path)
            useful_receipt = reconcile_artifact(feedback[1]["score"], useful_path)
            checks.update({
                "frame_reconciliation": len(arm["reconciliations"]) == 2 and
                    first_receipt == arm["reconciliations"][0]["reconciliation"] and
                    useful_receipt == arm["reconciliations"][1]["reconciliation"] and
                    first_receipt["matches"] is True and useful_receipt["matches"] is True,
                "pre_artifact": arm["metrics_ms"]["semantic_ready_to_image_ready_ms"] > 0,
                "probe_limit": max(arm["metrics_ms"]["first_probe_compute_ms"],
                    arm["metrics_ms"]["useful_probe_compute_ms"]) <=
                    plan["thresholds_ms"]["probe_compute_lte"],
            })
        arm_checks.append({"ordinal": ordinal, "mode": mode,
                           "passed": all(checks.values()), "checks": checks,
                           "events": len(events)})
        samples[mode].append(arm["metrics_ms"]["admission_to_semantic_ready_ms"])
        candidates.append(arm["candidate"]); programs.append(arm["program"])
    path_median = statistics.median(samples["path"])
    frame_median = statistics.median(samples["frame"])
    metrics = report["metrics_ms"]
    checks = {
        "frozen_sources": all((REPO/name).is_file() and sha(REPO/name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "allocation_passed": report["passed"] is True and all(report["checks"].values()),
        "all_arms": len(arm_checks) == 8 and all(row["passed"] for row in arm_checks),
        "order": [row["mode"] for row in arm_checks] == plan["order"],
        "same_candidate_program": all(row == candidates[0] for row in candidates) and
            all(row == programs[0] for row in programs),
        "medians": metrics["path_semantic_ready_median_ms"] == path_median and
            metrics["frame_semantic_ready_median_ms"] == frame_median and
            metrics["median_advantage_ms"] == path_median-frame_median,
        "limits": frame_median <= plan["thresholds_ms"]["frame_semantic_ready_median_lte"] and
            path_median <= plan["thresholds_ms"]["path_semantic_ready_median_lte"] and
            path_median-frame_median >= plan["thresholds_ms"]["median_advantage_gte"],
        "zero_model": report["model_calls"] == 0,
    }
    audit = {"schema": "matched-semantic-delivery-live-audit-v1",
             "passed": all(checks.values()), "checks": checks,
             "arm_checks": arm_checks, "metrics_ms": metrics, "scope": plan["scope"]}
    (root/"audit.json").write_text(json.dumps(audit, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
