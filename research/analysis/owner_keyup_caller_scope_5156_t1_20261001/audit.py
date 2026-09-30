"""Independent source/result auditor; does not import classify.py."""
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main():
    errors = []
    owner = ROOT / "source" / "owner_v10.py"
    wrapper = ROOT / "source" / "wrapper_v3.py"
    result_path = ROOT / "results" / "CLASSIFICATION.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    expected = {"owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
                "wrapper_v3.py": "0ea631abcf6272f0538a9ef9198ad8069b47b464"}
    observed = {"owner_v10.py": git_blob(owner), "wrapper_v3.py": git_blob(wrapper)}
    if observed != expected or result.get("source_git_blobs") != expected:
        errors.append("PINNED_SOURCE_BLOB_MISMATCH")
    tree = ast.parse(owner.read_bytes())
    run = next(n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "_run")
    release_calls = [n for n in ast.walk(run) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Name) and n.func.id == "release"]
    kinds = [site.get("kind") for site in result.get("owner_release_sites", [])]
    required = {"autonomous_stop", "autonomous_expiry_cancel_focus",
                "queued_explicit_release_or_close", "thread_finalizer"}
    if len(release_calls) != 4 or len(kinds) != 4 or set(kinds) != required:
        errors.append("RELEASE_CALLSITE_CLASSIFICATION_MISMATCH")
    if result.get("queued_explicit_site_count") != 1 or result.get("autonomous_site_count") != 3:
        errors.append("RELEASE_CALLSITE_COUNTS_MISMATCH")
    if result.get("wrapper_explicit_transition_branch") != "operation not in ('up', 'button_up')":
        errors.append("EXPLICIT_TRANSITION_BRANCH_MISMATCH")
    if result.get("wrapper_timestamps_explicit_up") is not True:
        errors.append("EXPLICIT_CALLER_BRACKET_NOT_FOUND")
    if result.get("wrapper_autonomous_cleanup_timer") is not False:
        errors.append("AUTONOMOUS_CLEANUP_TIMER_CLAIM_UNEXPECTED")
    if result.get("physical_keyup_or_application_consumption_measured") is not False:
        errors.append("SCOPE_OVERCLAIM")
    output = {
        "schema": "issue5156-caller-bracket-scope-audit-v1",
        "decision": "PASS_INDEPENDENT_AUDIT" if not errors else "STOP_AUDIT",
        "errors": errors,
        "checks": ["pinned_blobs", "four_release_sites", "explicit_vs_autonomous_split",
                   "wrapper_boundary", "scope_limit"],
        "source_git_blobs": observed,
        "classification_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
    }
    (ROOT / "results" / "AUDIT.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
