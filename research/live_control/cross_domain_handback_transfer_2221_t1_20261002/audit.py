"""Independent raw-only audit for the retained evidence transfer candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def read_pinned(repo_root, pins):
    loaded = {}
    errors = []
    for relative, expected in pins["sources"].items():
        data = (repo_root / relative).read_bytes()
        observed = hashlib.sha256(data).hexdigest()
        git_blob = subprocess.run(
            ["git", "rev-parse", f"{pins['main_sha']}:{relative}"],
            cwd=repo_root, capture_output=True, text=True, check=True).stdout.strip()
        if observed != expected["sha256"]:
            errors.append(f"source_hash:{relative}")
        if git_blob != expected["git_blob_sha1"]:
            errors.append(f"source_git_blob:{relative}")
        loaded[relative] = (data, observed)
    return loaded, errors


def verify_freeze(package, freeze_path):
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    errors = []
    for relative, expected in freeze["sha256"].items():
        observed = hashlib.sha256((package / relative).read_bytes()).hexdigest()
        if observed != expected:
            errors.append(f"frozen_source:{relative}")
    return errors


def audit_candidate(candidate, repo_root, package, freeze_errors=None):
    freeze_errors = freeze_errors or []
    pins = json.loads((package / "SOURCE_HASHES.json").read_text(encoding="utf-8"))
    cases = json.loads((package / "cases.json").read_text(encoding="utf-8"))
    loaded, errors = read_pinned(repo_root, pins)
    by_path = {path: json.loads(data.decode("utf-8"))
               for path, (data, _) in loaded.items() if path.endswith(".json")}
    doom_path = "research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json"
    audit_path = "runtime/results/public-six-task-comparison-04/audit.json"
    task6_path = "runtime/results/public-six-task-comparison-04/task6-visual-audit.json"
    doom = by_path[doom_path]
    public_audit = by_path[audit_path]
    task6 = by_path[task6_path]["task6"]
    runs = {row["run"]: row for row in doom["runs"]}
    v38 = runs["map01-v38-integrated-threat-live-01"]
    v39 = runs["map01-v39-coast-liveness-live-01"]
    records = candidate.get("records") if isinstance(candidate, dict) else None
    records = records if isinstance(records, list) else []
    rows = {row.get("case_id"): row for row in records if isinstance(row, dict)}
    expected_ids = cases["cases"]

    checks = {}
    checks["source_hashes_match"] = not errors
    checks["scoped_identity_and_case_set"] = (
        candidate.get("experiment_id") == cases["experiment_id"]
        and candidate.get("status") == "PASS_RETAINED_SOURCE_TRANSFER_CANDIDATE"
        and candidate.get("scope") ==
        "read-only retained-evidence projection; no model/GUI/input/live task"
        and len(records) == len(expected_ids)
        and len(rows) == len(expected_ids)
        and set(rows) == set(expected_ids))

    v38_row = rows.get("doom-v38-first-plan-frame", {})
    v39_row = rows.get("doom-v39-first-plan-frames", {})
    expected_v38 = v38["first_exact_plan_feedback"][0]
    expected_v39 = v39["first_exact_plan_feedback"]
    def expected_source(path, field):
        return {"artifact": path,
                "sha256": pins["sources"][path]["sha256"],
                "field": field}

    checks["source_lineage_pinned"] = (
        rows.get("doom-v38-first-plan-frame", {}).get("source") == expected_source(
            doom_path,
            "runs[map01-v38-integrated-threat-live-01].first_exact_plan_feedback[0]")
        and rows.get("doom-v39-first-plan-frames", {}).get("source") == expected_source(
            doom_path,
            "runs[map01-v39-coast-liveness-live-01].first_exact_plan_feedback")
        and rows.get("doom-v39-typed-revocation-release", {}).get("source") == expected_source(
            doom_path,
            "runs[map01-v39-coast-liveness-live-01].running_release_latency")
        and rows.get("browser-direct-task6-save", {}).get("source") == expected_source(
            task6_path, "task6")
        and rows.get("browser-direct-task6-save", {}).get("crosscheck_source") == expected_source(
            audit_path, "routes.direct.exact_tasks / acceptance"))
    checks["doom_observed_change_stays_unresolved"] = (
        v38_row.get("evidence_type") == "OBSERVED_CHANGE"
        and v38_row.get("task_effect") == "UNRESOLVED"
        and v38_row.get("semantic_task_feedback") == "unverified"
        and v38_row.get("first_exact_capture_ms") == expected_v38["first_exact_capture_ms"]
        and v39_row.get("evidence_type") == "OBSERVED_CHANGE"
        and v39_row.get("task_effect") == "UNRESOLVED"
        and v39_row.get("semantic_task_feedback") == "unverified"
        and v39_row.get("frame_count") == len(expected_v39) == 3
        and v39_row.get("frame_capture_ms") ==
        [x["first_exact_capture_ms"] for x in expected_v39]
        and v39_row.get("lineage") == [x["id"] for x in expected_v39])
    checks["doom_progress_not_terminal"] = (
        v38_row.get("map_exit") is False
        and v39_row.get("map_exit") is v39["totals"]["independent_map_exit"] is False
        and v39_row.get("independent_kills") == v39["totals"]["independent_kills"] == 1
        and v39_row.get("independent_deaths") == v39["totals"]["independent_deaths"] == 0
        and v39_row.get("task_terminal") == "NOT_ESTABLISHED")

    release_row = rows.get("doom-v39-typed-revocation-release", {})
    release = v39["running_release_latency"][0]
    checks["release_not_task_effect"] = (
        release_row.get("evidence_type") == "PHYSICAL_RELEASE"
        and release_row.get("physical_release") == "VERIFIED"
        and release_row.get("task_effect") == "UNRESOLVED"
        and release_row.get("capture_to_release_ms") == release["capture_to_verified_physical_release_ms"]
        and release_row.get("typed_emit_to_release_ms") == release["typed_emit_to_verified_physical_release_ms"]
        and release_row.get("release_to_terminal_ms") == release["verified_physical_release_to_terminal_ms"])

    desktop = rows.get("browser-direct-task6-save", {})
    checks["desktop_independent_effect_matches_source"] = (
        public_audit.get("status") == "PASS_PUBLIC_SIX_TASK_CORRECTNESS_SCOPED"
        and public_audit.get("raw_files") == 1051
        and desktop.get("evidence_type") == "TASK_EFFECT"
        and desktop.get("task_effect") == "EXACT_ONCE_SUBMISSION"
        and desktop.get("independently_scored") is True
        and desktop.get("call_id") == task6["call_id"]
        and desktop.get("submission_count") == 1
        and task6["submission"]["exact"] is True
        and task6["submission"]["submitted_values"] == ["t992004-6"])
    checks["visual_ack_remains_unknown"] = (
        desktop.get("visual_acknowledgement") == "UNKNOWN_NOT_OBSERVED"
        and task6["visual_cue_after_fresh_observation"] == "UNKNOWN_NOT_OBSERVED"
        and desktop.get("physical_release_verified") is True
        and task6["save_release_verified"] is True
        and task6["close_release_verified"] is True)

    checks["no_authority_or_cross_source_clock_join"] = all(
        row.get("input_authority") is False
        and row.get("semantic_authority") is False
        and row.get("clock_join") in {"NOT_CLAIMED", "WITHIN_SOURCE_EVENT_ONLY"}
        for row in records)
    checks["frozen_candidate_and_auditor_unchanged"] = not freeze_errors
    failed = [name for name, ok in checks.items() if not ok]
    status = "PASS_RETAINED_EVIDENCE_TRANSFER_SCOPED" if not failed else "FAIL_AUDIT"
    return {
        "experiment_id": cases["experiment_id"], "status": status,
        "checks": checks, "checks_passed": sum(checks.values()),
        "checks_total": len(checks), "failed_checks": failed,
        "source_hash_errors": errors,
        "freeze_hash_errors": freeze_errors,
        "limits": "No model recovery, live cross-domain efficacy, useful DOOM feedback, latency, or product transfer is established.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze", type=Path)
    args = parser.parse_args()
    freeze_errors = (verify_freeze(Path(__file__).resolve().parent, args.freeze)
                     if args.freeze else [])
    result = audit_candidate(json.loads(args.candidate.read_text(encoding="utf-8")),
                             args.repo_root.resolve(), Path(__file__).resolve().parent,
                             freeze_errors)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "checks_passed": result["checks_passed"],
                      "checks_total": result["checks_total"],
                      "failed_checks": result["failed_checks"]}))
    if result["status"] != "PASS_RETAINED_EVIDENCE_TRANSFER_SCOPED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
