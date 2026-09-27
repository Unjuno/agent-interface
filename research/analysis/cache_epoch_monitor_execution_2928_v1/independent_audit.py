"""Independently recompute the reported boundary counts from retained rows."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
manifest = json.loads((HERE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
subject = ROOT / result["subject_path"]
runner = HERE / "model_check.py"
audit_source = HERE / "independent_audit.py"
subject_git_blob_sha = subprocess.check_output(
    ["git", "hash-object", f"--path={result['subject_path']}", result["subject_path"]],
    cwd=ROOT,
    text=True,
).strip()
rows = result["rows"]
expected_states = {
    (epoch, complete)
    for epoch in ("same", "changed", "missing")
    for complete in (True, False)
}
observed_states = {(row["request_epoch"], row["dependencies_complete"]) for row in rows}
recomputed_oracle = [
    row["request_epoch"] == "same" and row["dependencies_complete"] for row in rows
]
recomputed_unsafe = [
    row["candidate_disposition"] == "KEEP" and not allowed
    for row, allowed in zip(rows, recomputed_oracle, strict=True)
]
checks = {
    "subject_hash_matches": hashlib.sha256(subject.read_bytes()).hexdigest()
    == result["subject_sha256"],
    "source_manifest_matches_subject": manifest["subject_sha256"]
    == result["subject_sha256"],
    "source_manifest_matches_main_blob": subject_git_blob_sha
    == manifest["subject_main_git_blob_sha"],
    "source_manifest_matches_runner": hashlib.sha256(runner.read_bytes()).hexdigest()
    == manifest["runner_sha256"],
    "source_manifest_matches_auditor": hashlib.sha256(audit_source.read_bytes()).hexdigest()
    == manifest["auditor_sha256"],
    "complete_six_state_cross_product": len(rows) == 6 and observed_states == expected_states,
    "rows_all_use_candidate_keep": all(row["candidate_disposition"] == "KEEP" for row in rows),
    "row_oracle_matches_explicit_gate": all(
        row["oracle_replay_allowed"] == allowed
        for row, allowed in zip(rows, recomputed_oracle, strict=True)
    ),
    "candidate_keep_count": result["candidate_keep"] == 6,
    "oracle_allow_count": result["oracle_allowed"] == sum(recomputed_oracle) == 1,
    "unsafe_keep_count": result["unsafe_keep"] == sum(recomputed_unsafe) == 5,
    "unrepresented_required_fields": set(result["missing_required_fields"])
    == {"request_epoch", "dependency_completeness"},
    "scoped_failure_label": result["decision"] == "FAIL_REPLAY_SAFETY_BOUNDARY_SCOPED",
}
audit = {
    "schema": "cache_epoch_monitor_execution_audit_2928_v1",
    "checks": checks,
    "passed": all(checks.values()),
    "errors": [name for name, passed in checks.items() if not passed],
    "method": "Raw-row and source-hash audit; does not import or execute candidate code.",
}
(HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("AUDIT_PASS" if audit["passed"] else json.dumps(audit, sort_keys=True))
