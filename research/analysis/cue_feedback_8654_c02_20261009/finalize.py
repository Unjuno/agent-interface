#!/usr/bin/env python3
"""Create an immutable execution/result receipt after the one-shot workflow."""
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

candidate_outcome = os.environ.get("CANDIDATE_OUTCOME", "unknown")
raw_upload_outcome = os.environ.get("RAW_UPLOAD_OUTCOME", "unknown")
audit_outcome = os.environ.get("AUDIT_OUTCOME", "unknown")
raw_path = RESULTS / "candidate.jsonl"
receipt_path = RESULTS / "candidate_receipt.json"
audit_path = RESULTS / "audit.json"
audit = read_json(audit_path)
receipt = read_json(receipt_path)
if candidate_outcome != "success":
    disposition = "STOP_CANDIDATE_FAILED"
elif raw_upload_outcome != "success":
    disposition = "STOP_RAW_CUSTODY_NOT_RETAINED"
elif audit_outcome != "success" or not audit or audit.get("integrity_status") != "PASS_METHOD_SCOPED":
    disposition = "FAIL_OR_STOP_AUDIT"
else:
    disposition = "PASS_METHOD_SCOPED"

repo_root = ROOT.parents[2]
workflow_path = repo_root / ".github" / "workflows" / "issue-8654-c02.yml"
run = {
    "allocation": "8654-C02",
    "disposition": disposition,
    "candidate_invocations": 1 if candidate_outcome != "skipped" else 0,
    "auditor_invocations": 1 if audit_outcome != "skipped" else 0,
    "candidate_step_outcome": candidate_outcome,
    "pre_audit_raw_artifact_upload_outcome": raw_upload_outcome,
    "auditor_step_outcome": audit_outcome,
    "source_commit": os.environ.get("GITHUB_SHA"),
    "base_main_sha_at_preregistration": "9f67de666b640997ed7cb27cbe278ef19677be5d",
    "branch": os.environ.get("GITHUB_REF_NAME"),
    "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
    "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
    "workflow_run_url": (
        os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        + "/" + os.environ.get("GITHUB_REPOSITORY", "")
        + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "")
    ),
    "runner_os": os.environ.get("RUNNER_OS"),
    "runner_image": os.environ.get("ImageOS"),
    "python": sys.version,
    "platform": platform.platform(),
    "source_sha256": {
        "PREREG.md": sha256(ROOT / "PREREG.md"),
        "candidate.py": sha256(ROOT / "candidate.py"),
        "audit.py": sha256(ROOT / "audit.py"),
        "finalize.py": sha256(ROOT / "finalize.py"),
        "workflow.yml": sha256(workflow_path),
    },
    "candidate_receipt": receipt,
    "audit_sha256": sha256(audit_path) if audit_path.exists() else None,
    "audit_result": audit,
    "raw_sha256": sha256(raw_path) if raw_path.exists() else None,
    "raw_bytes": raw_path.stat().st_size if raw_path.exists() else None,
    "notes": [
        "The workflow attempts to upload raw candidate output and receipt before audit; the recorded step outcome determines whether audit was permitted.",
        "On successful audit and publication, raw, receipt, audit, execution record, and report are committed under this allocation's additive results/ path.",
        "No candidate or auditor retry is permitted; this is a new successor allocation, not a rerun of C01.",
    ],
}
(RESULTS / "EXECUTION.json").write_text(
    json.dumps(run, sort_keys=True, indent=2, allow_nan=False) + "\n",
    encoding="utf-8",
)
lines = [
    "# Issue #8654 C02 — result",
    "",
    f"Disposition: {disposition}",
    "",
    f"Source commit: {run['source_commit']}",
    f"Workflow run: {run['workflow_run_url']}",
    f"Runner: {run['runner_image']} / Python {sys.version.split()[0]}",
    "",
]
if audit:
    lines += [
        f"Integrity: {audit.get('integrity_status')}",
        f"Study outcome: {audit.get('study_outcome')}",
        f"Stable fully supported wrong rows: {audit.get('stable_supported_error_rows')}",
        f"Stable fully supported wrong probability mass: {audit.get('stable_supported_error_probability_mass')}",
        "",
        "| Regime | Complete-support mass | Correct mass | Error mass | Accuracy among supported |",
        "|---|---:|---:|---:|---:|",
    ]
    for regime in ("STABLE", "REVERSAL", "GLOBAL_SHIFT"):
        def value(obj, key):
            return (obj or {}).get(regime)
        lines.append(
            f"| {regime} | {value(audit.get('complete_support_probability_mass'), regime)} "
            f"| {value(audit.get('correct_probability_mass'), regime)} "
            f"| {value(audit.get('supported_error_probability_mass'), regime)} "
            f"| {value(audit.get('accuracy_conditional_on_complete_support'), regime)} |"
        )
    lines += ["", f"Raw JSONL SHA-256: {run['raw_sha256']} ({run['raw_bytes']} bytes).", ""]
lines += [
    "## Scope",
    "",
    "This is an exact deterministic finite-sample method result only. It does not test stochastic rewards, propensity misspecification, sequential learning, GUI behavior, user outcomes, runtime benefit, or safety. The C01 raw-custody STOP remains unchanged.",
    "",
    "The pre-audit raw artifact must have succeeded before an auditor invocation is counted. No retry was authorized or performed.",
]
(RESULTS / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({"disposition": disposition, "audit": audit}, sort_keys=True))
