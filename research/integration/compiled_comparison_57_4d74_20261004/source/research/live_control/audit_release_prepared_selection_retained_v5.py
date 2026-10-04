"""Audit retained pre-artifact semantic feedback evidence."""
import hashlib
import json
from pathlib import Path

from executor_v11 import program_sha256
from inkscape_selection_frame_probe_v1 import reconcile_artifact
from inkscape_selection_scorer_v2 import score


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/release-prepared-selection-live-05"


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
    retention = read(ROOT/"retention.json")
    plan = read(ROOT/"preregistration.json")
    report, audit = read(ROOT/"report.json"), read(ROOT/"audit.json")
    probes = report["semantic_scores"]
    feedback = report["selection_observation"]
    useful = report["semantic_observation"]
    feedback_path = ROOT/Path(feedback["image"]).name
    useful_path = ROOT/Path(useful["image"]).name
    old_first = score(report["clients"]["early"]["candidate"], feedback_path)
    old_useful = score(report["clients"]["early"]["candidate"], useful_path)
    first_receipt = reconcile_artifact(probes[0]["score"], feedback_path)
    useful_receipt = reconcile_artifact(probes[-1]["score"], useful_path)
    terminal = report["selection_terminal"]
    metrics = report["metrics_ms"]
    checks = {
        "manifest": all(sha(ROOT/name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all((REPO/name).is_file() and sha(REPO/name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "first_pass": (retention["decision"] == "RETAIN_FIRST_OUTCOME_NO_RETRY" and
                       report["passed"] is True and audit["passed"] is True),
        "program_attested": (report["selection_accepted"]["steps"] == 2 and
            report["selection_accepted"]["program_sha256"] ==
            program_sha256(report["selection_program"])),
        "false_then_true": (len(probes) == 2 and probes[0]["score"]["success"] is False and
            probes[1]["score"]["success"] is True and
            useful["sequence"] > feedback["sequence"]),
        "independent_semantics": (semantic(probes[0]["score"]) == semantic(old_first) and
            semantic(probes[1]["score"]) == semantic(old_useful)),
        "artifact_reconciliation": (first_receipt["matches"] is True and
            useful_receipt["matches"] is True and
            first_receipt == report["semantic_probe_reconciliations"][0]["reconciliation"] and
            useful_receipt == report["semantic_probe_reconciliations"][1]["reconciliation"]),
        "pre_artifact_order": all(probe["probe_completed_ns"] < reconciliation["image_ready_ns"]
            for probe, reconciliation in zip(probes,
                report["semantic_probe_reconciliations"])),
        "client_before_terminal": (metrics["semantic_client_to_terminal_ms"] > 0 and
            report["semantic_feedback_received_ns"] < terminal["terminal_ns"]),
        "terminal_release": (terminal["status"] == "completed" and
            terminal["steps_completed"] == 2 and terminal["release"]["verified"] is True and
            terminal["release"]["keys_down"] == [] and terminal["release"]["buttons_down"] == []),
        "timing": (metrics["selection_admission_to_semantic_feedback_received_ms"] <=
            plan["thresholds_ms"]["admission_to_semantic_client_lte"] and
            max(metrics["first_probe_compute_ms"], metrics["useful_probe_compute_ms"]) <=
            plan["thresholds_ms"]["probe_compute_lte"]),
        "zero_model_retry": report["model_calls"] == report["retry_count"] == 0,
    }
    result = {"passed": all(checks.values()), "checks": checks,
              "metrics_ms": metrics, "files_in_manifest": len(retention["manifest"]),
              "bytes_before_receipt": retention["bytes"], "scope": report["scope"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
                                            encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
