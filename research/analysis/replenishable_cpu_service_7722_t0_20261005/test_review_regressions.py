"""Review regressions for the supplemental retained-evidence audit."""

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("review_audit", ROOT / "review_audit.py")
review_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review_audit)
CFG = json.loads((ROOT / "cases.json").read_text())
RAW = json.loads((ROOT / "output/candidate/candidate.raw.json").read_text())


def _run(case_id, policy):
    return copy.deepcopy(next(r for r in RAW["runs"] if r["case_id"] == case_id and r["policy"] == policy))


def _case(case_id):
    return next(c for c in CFG["cases"] if c["case_id"] == case_id)


def test_original_retained_runs_follow_reconstructed_dispatch():
    for run in RAW["runs"]:
        assert review_audit.check_run(run, CFG, _case(run["case_id"])) == []


def test_swapped_control_and_best_effort_dispatch_is_rejected():
    case_id = "sched_seed_7722"
    run = _run(case_id, "shared_priority")
    first = next(e for e in run["events"] if e["tick"] == 1000)
    second = next(e for e in run["events"] if e["tick"] == 1004)
    first["job_id"], second["job_id"] = second["job_id"], first["job_id"]
    first["job_class"], second["job_class"] = second["job_class"], first["job_class"]
    rows = {row["job_id"]: row for row in run["jobs"]}
    rows[f"{case_id}-c0"]["finish_tick"] = 1005
    rows[f"{case_id}-b1-0"]["finish_tick"] = 1009
    errors = review_audit.check_run(run, CFG, _case(case_id))
    assert "dispatch_order" in errors
    assert review_audit.mutation_rejected(run, CFG, _case(case_id)) is True


def test_backpressure_rejection_before_queue_full_is_rejected():
    case_id = "sched_seed_7722"
    run = _run(case_id, "shared_backpressure")
    rejected_id = f"{case_id}-b9-13"
    rows = {row["job_id"]: row for row in run["jobs"]}
    rows[rejected_id]["status"] = "rejected_backpressure"
    run["rejected_best_effort"].append(rejected_id)
    errors = review_audit.check_run(run, CFG, _case(case_id))
    assert "invalid_backpressure_admission" in errors
    assert review_audit.mutation_rejected(run, CFG, _case(case_id)) is True


def test_mutation_probe_does_not_treat_nonempty_report_as_rejection():
    run = _run("sched_seed_7722", "shared_priority")
    assert review_audit.mutation_rejected(run, CFG, _case("sched_seed_7722")) is False


def test_read_only_reaudit_reconstructs_all_retained_runs_and_controls():
    result = review_audit.audit_retained_raw(RAW, CFG)
    assert result["status"] == "PASS_SUPPLEMENTAL_RAW_RECONSTRUCTION"
    assert result["raw_run_count"] == 18
    assert result["raw_reconstruction_errors"] == []
    assert result["mutation_controls"]["control_priority_fifo_violation"]["rejected"] is True
    assert result["mutation_controls"]["backpressure_rejection_before_capacity"]["rejected"] is True
    assert len(result["mutation_controls"]) == 8
    assert all(control["rejected"] for control in result["mutation_controls"].values())
    assert result["unchanged_trace_control"]["accepted"] is True
    assert result["candidate_invocations"] == result["frozen_auditor_invocations"] == 0


def test_verifier_uses_explicit_checks_and_requires_raw_and_audit_entries():
    source = (ROOT / "verify_retained.py").read_text(encoding="utf-8")
    assert "assert " not in source
    assert "REQUIRED_MANIFEST_FILES" in source


def test_verifier_rejects_manifest_omission_and_corruption_under_optimized_python(tmp_path):
    package = tmp_path / "package"
    import shutil

    shutil.copytree(ROOT, package, ignore=shutil.ignore_patterns("__pycache__"))
    valid = subprocess.run([sys.executable, "-O", str(package / "verify_retained.py")], capture_output=True, text=True)
    assert valid.returncode == 0
    assert "PASS_RETAINED_PACKAGE_INTEGRITY_WITH_SUPPLEMENTAL_AUDIT" in valid.stdout
    sums = package / "SHA256SUMS"
    entries = sums.read_text().splitlines()
    sums.write_text("\n".join(line for line in entries if not line.endswith("  output/candidate/candidate.raw.json")) + "\n")
    (package / "output/candidate/candidate.raw.json").write_text("{}\n")
    result = subprocess.run([sys.executable, "-O", str(package / "verify_retained.py")], capture_output=True, text=True)
    assert result.returncode != 0
    assert "PASS_RETAINED_EVIDENCE_INTEGRITY" not in result.stdout
