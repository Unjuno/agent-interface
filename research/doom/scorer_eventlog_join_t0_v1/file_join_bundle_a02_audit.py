"""Verify A02 raw outcomes and exact Git source lineage independently."""
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
FREEZE_PATH = ROOT / "FILE_JOIN_BUNDLE_A02_FREEZE.json"
RAW_PATH = ROOT / "file_join_bundle_a02_raw.json"


def _git_blob(revision, path):
    result = subprocess.run(
        ["git", "rev-parse", f"{revision}:research/{path}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def audit():
    freeze_bytes = FREEZE_PATH.read_bytes()
    freeze = json.loads(freeze_bytes)
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    errors = []
    if raw.get("schema") != "scorer-eventlog-run-bundle-raw-v2":
        errors.append("schema")
    if raw.get("base_main") != freeze.get("base_main"):
        errors.append("base_main")
    if raw.get("stack_parent") != freeze.get("stack_parent"):
        errors.append("stack_parent")
    if raw.get("freeze_sha256") != hashlib.sha256(freeze_bytes).hexdigest():
        errors.append("freeze_hash")
    if raw.get("source_sha256") != freeze.get("required_source_sha256"):
        errors.append("source_sha256")
    if raw.get("source_git_blob") != freeze.get("required_source_git_blob"):
        errors.append("source_git_blob")
    if raw.get("launch_scope") != freeze.get("launch_scope"):
        errors.append("launch_scope")

    for name, expected in freeze["required_source_git_blob"].items():
        for revision in (freeze["base_main"], freeze["stack_parent"]):
            try:
                if _git_blob(revision, name) != expected:
                    errors.append(f"git_blob:{revision}:{name}")
            except (OSError, subprocess.CalledProcessError):
                errors.append(f"git_object_missing:{revision}:{name}")
        path = REPO_ROOT / "research" / Path(*name.split("/"))
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            actual = None
        if actual != freeze["required_source_sha256"].get(name):
            errors.append(f"working_tree_source_hash:{name}")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", freeze["stack_parent"], "HEAD"],
        cwd=REPO_ROOT, capture_output=True)
    if ancestry.returncode != 0:
        errors.append("stack_parent_not_ancestor")

    expected = freeze.get("cases", {})
    rows = raw.get("cases")
    if not isinstance(rows, list) or len(rows) != len(expected):
        errors.append("case_count")
        rows = rows if isinstance(rows, list) else []
    seen = set()
    for row in rows:
        case_id = row.get("id")
        if case_id not in expected or case_id in seen:
            errors.append(f"unexpected_or_duplicate:{case_id}")
            continue
        seen.add(case_id)
        result = row.get("observed")
        if row.get("expected") != expected[case_id]:
            errors.append(f"frozen_expectation:{case_id}")
        if not isinstance(result, dict):
            errors.append(f"missing_result:{case_id}")
            continue
        if result.get("decision") != expected[case_id]:
            errors.append(f"decision:{case_id}")
        if result.get("causal_attribution") is not False:
            errors.append(f"causal_scope:{case_id}")
        if case_id == "valid_bundle":
            if result.get("reason") != freeze["decision_gates"]["valid_bundle_reason"]:
                errors.append("valid_reason")
            if result.get("positive_sample_ns") != 130:
                errors.append("valid_positive_sample")
        elif result.get("reason") != freeze["decision_gates"]["invalid_bundle_reason"]:
            errors.append(f"invalid_reason:{case_id}")
    if seen != set(expected):
        errors.append("case_completeness")
    return {"schema": "scorer-eventlog-run-bundle-audit-v2",
            "pass": not errors, "errors": errors, "rows": len(rows),
            "verified_git_trees": [freeze["base_main"], freeze["stack_parent"]],
            "claim_scope": "synthetic MAP01 run-bundle consumer construction only"}


if __name__ == "__main__":
    result = audit()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (ROOT / "file_join_bundle_a02_audit.json").write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if result["pass"] else 1)
