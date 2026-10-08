"""Independent raw-result checks for the Issue #2922 GET first-rung."""
import hashlib
import json
from pathlib import Path
import subprocess

SOURCES = {
    "research/live_control/executor_v3.py": "ea3fa8c9751a6a41b4814ad6e0d03bec85166765b0a41d2488a51750d17b3a4a",
    "research/live_control/lease.py": "e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f",
    "research/live_control/session_v4.py": "04f06d7b787baa77cae20d0c51b563ccc4985dc19b47308d7c24318c5a9e7fee",
    "research/observation_gating/exact_gate.py": "6780624513a95039657734e76c0420447a3f9ab49f98e1f3137a19a91bc31944",
    "research/observation_gating/gui_suite.py": "953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f",
    "research/observation_tiles/image_artifact.py": "7bf6b71d811aaefa75e87f5d9d20fd9275fc928104e910deaca9e3f00c55363e",
    "research/observation_tiles/tile_transport.py": "f74caf4f2bea59fe3a73b3f04975384d8520bb06c296765566c4dd2542ef12b0",
    "research/real_apps_v1/real_app_suite_v1.py": "22b4cc86af68a0ae866fe24735faaeefa40c0e1722238ab8c04723e1a564db24",
}

def audit(result, source_root):
    errors = []
    checks = {
        "schema": result.get("schema") == "issue2922_private_endpoint_get_probe_v1",
        "allocation": result.get("allocation") == "issue2922-private-endpoint-get-20260927-r1",
        "seed": result.get("seed") == 992925,
        "repository_commit": result.get("repository_commit") == "01349d7bc76e5635f5568c53ffeec4d9ff49abb1",
        "runtime_image": result.get("runtime_image") == "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393",
        "runtime": result.get("runtime") == "CPython 3.11.2",
        "exit_zero": result.get("container_exit_code") == 0,
        "session_ready": result.get("session_ready") is True,
        "private_loopback": result.get("session_endpoint_host") == "127.0.0.1",
        "GET_only": result.get("request_method") == "GET",
        "HTTP_200": result.get("http_status") == 200,
        "marker": result.get("body_contains_ready_marker") is True,
        "body_size": result.get("body_bytes") == 187,
        "no_output_before": result.get("output_exists_before") is False,
        "no_output_after": result.get("output_exists_after") is False,
        "no_probe_POST": result.get("probe_POST_calls_issued") == 0,
        "not_task_allocated": result.get("task_allocated") is False,
        "no_input": result.get("gui_input") is False,
        "no_model": result.get("model_calls") == 0,
        "honest_POST_scope": result.get("server_POST_count") == "not instrumented",
        "scoped_disposition": result.get("disposition") == "PASS_PRIVATE_ENDPOINT_GET_NO_OUTPUT_MUTATION",
    }
    errors.extend(name for name, ok in checks.items() if not ok)
    reported = result.get("source_sha256", {})
    if reported != SOURCES:
        errors.append("source_manifest_values")
    probe_path = (Path(source_root) / "research/integration/"
                  "golden_ipc_source_closure_2922_v1/endpoint_get_probe.py")
    if (not probe_path.is_file()
            or hashlib.sha256(probe_path.read_bytes()).hexdigest()
            != result.get("probe_source_sha256")):
        errors.append("probe_source_hash")
    manifest_rel = ("research/integration/golden_ipc_source_closure_2922_v1/"
                    "SOURCE_MANIFEST.json")
    try:
        manifest_proc = subprocess.run(
            ["git", "-C", str(source_root), "show", "origin/main:" + manifest_rel],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if manifest_proc.returncode:
            manifest_proc = subprocess.run(
                ["git", "-C", str(source_root), "show", "HEAD:" + manifest_rel],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if manifest_proc.returncode:
            raise OSError("manifest git object unavailable")
        manifest = json.loads(manifest_proc.stdout)
        if manifest.get("commit") != result.get("repository_commit"):
            errors.append("manifest_commit")
        manifest_sha = {path: item.get("sha256") for path, item in manifest.get("files", {}).items()}
        if manifest_sha != SOURCES:
            errors.append("manifest_source_values")
    except (OSError, ValueError):
        errors.append("manifest_unavailable")
    for rel, expected in SOURCES.items():
        proc = subprocess.run(
            ["git", "-C", str(source_root), "show",
             result.get("repository_commit", "") + ":" + rel],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode or hashlib.sha256(proc.stdout).hexdigest() != expected:
            errors.append("source_hash:" + rel)
    return {"schema": "issue2922_private_endpoint_get_audit_v1",
            "checks": checks, "errors": errors,
            "verdict": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT"}

def main():
    here = Path(__file__).resolve().parent
    repo = here.parents[3]
    result = json.loads((here / "RESULT.json").read_text())
    report = audit(result, repo)
    (here / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if not report["errors"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
