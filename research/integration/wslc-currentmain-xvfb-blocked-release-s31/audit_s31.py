#!/usr/bin/env python3
"""Independent audit of retained S31 WSLc readiness and cleanup receipts."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
external = Path(sys.argv[1]).resolve()
attempt = "wslc-standard-caller-xvfb-20261025-s31-0fc5b445d5c4"
prereg = json.loads((root / "PREREGISTRATION.json").read_text())
conditions = json.loads((root / "CONDITIONS.json").read_text())
freeze = json.loads((root / "SOURCE-FREEZE.json").read_text())
reuse = json.loads((root / "INPUT-REUSE-AUDIT.json").read_text())
events = [json.loads(line) for line in (external / "raw-harness-output.jsonl").read_text().splitlines() if line.strip()]
stages = [event["stage"] for event in events]
polls = [event["details"] for event in events if event["stage"] == "exact_name_preflight_poll"]
cleanup = json.loads((external / "output" / "resource-cleanup.json").read_text())
storage = Path(cleanup["storagePath"])
host_source = (root / "harness" / "Program.cs").read_text()
checks = {
    "attempt_binding": prereg["attempt_id"] == conditions["attempt_id"] == freeze["attempt_id"] == attempt,
    "source_still_current_main": freeze["source_commit"] == freeze["local_head"] == freeze["github_main"] == "c3a6bb2fe715e0ad3d1b0c3cd13a5d8c080dbaf0",
    "input_reuse_audit": reuse["passed"] == reuse["total"] == 7 and all(reuse["checks"].values()),
    "fresh_unique_session": prereg["session_name"] == cleanup["sessionName"] == "agent-interface-wslc-s31-0fc5b445d5c4",
    "one_session_start_and_termination": stages.count("session_started") == stages.count("session_terminated") == 1 and cleanup.get("started") and cleanup.get("terminated"),
    "exact_name_scoped_polls": len(polls) == 10 and all(p.get("filter") == "name=" + prereg["container_name"] for p in polls),
    "all_polls_same_path_error": all(p.get("exit") == 1 and p.get("stdout", "") == "" and "ERROR_PATH_NOT_FOUND" in p.get("stderr", "") for p in polls),
    "preflight_timed_out_as_preregistered": stages.count("failure") == 1 and any("did not pass within 10 polls" in e.get("details", {}).get("message", "") for e in events if e["stage"] == "failure"),
    "no_container_or_image_pull": "container_created" not in stages and "image_pull_complete" not in stages and cleanup.get("cid") is None and not cleanup.get("pulled"),
    "task_body_not_started": not (external / "output" / "trial-started.txt").exists() and not (external / "output" / "result.json").exists(),
    "cleanup_receipt_has_no_pending_container_or_image": not cleanup.get("deleted") and not cleanup.get("imageDeleted"),
    "storage_directory_empty": storage.exists() and not any(storage.iterdir()),
    "bounded_preflight_in_source": "poll<=10" in host_source and "WaitForExit(2000)" in host_source and '"--session",sessionName,"container","list","--all","--filter","name="+containerName' in host_source,
    "no_global_inventory_or_docker_in_source": '"session","list"' not in host_source and '"image","ls"' not in host_source and "docker.exe" not in host_source.lower(),
    "no_task_retry": stages.count("container_created") == 0 and stages.count("exact_name_preflight_poll") == 10,
}
result = {
    "schema": "agent-interface/wslc-s31-independent-audit-v1",
    "attempt_id": attempt,
    "classification": "HOLD_PRETRIAL_SESSION_READINESS_PATH_NOT_FOUND",
    "audited_without_runtime_import": True,
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "failed": [key for key, value in checks.items() if not value],
    "observations": {
        "readiness_polls": len(polls),
        "readiness_failures": [p.get("stderr", "").split("\n")[1:2] for p in polls],
        "formal_invocation_exit_code": 1,
        "task_input_started": False,
        "container_created": False,
        "image_pulled": False,
        "session_terminated": cleanup.get("terminated"),
        "session_storage_empty": not any(storage.iterdir()),
    },
}
(root / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"classification": result["classification"], "passed": result["passed"], "total": result["total"], "failed": result["failed"]}, sort_keys=True))
