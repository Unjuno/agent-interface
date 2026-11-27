#!/usr/bin/env python3
"""Audit only retained S30 setup receipts; never imports the runtime candidate."""
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
external = Path(sys.argv[1]).resolve()
attempt = "wslc-standard-caller-xvfb-20261025-s30-a57146d1c900"
prereg = json.loads((root / "PREREGISTRATION.json").read_text())
conditions = json.loads((root / "CONDITIONS.json").read_text())
source = json.loads((root / "SOURCE-FREEZE.json").read_text())
input_audit = json.loads((root / "INPUT-AUDIT.json").read_text())
events = [json.loads(line) for line in (external / "raw-harness-output.jsonl").read_text().splitlines() if line.strip()]
cleanup = json.loads((external / "output" / "resource-cleanup.json").read_text())
host_source = (root / "harness" / "Program.cs").read_text()
stages = [event["stage"] for event in events]
preflight = next((e["details"] for e in events if e["stage"] == "exact_name_preflight"), {})
storage = Path(cleanup["storagePath"])
checks = {
    "attempt_binding": prereg["attempt_id"] == conditions["attempt_id"] == source["attempt_id"] == attempt,
    "source_main_frozen": source["source_commit"] == source["github_main"] == "c3a6bb2fe715e0ad3d1b0c3cd13a5d8c080dbaf0",
    "input_audit_passed": input_audit["passed"] == input_audit["total"] == 13 and all(input_audit["checks"].values()),
    "unique_named_session": prereg["session_name"] == cleanup["sessionName"] == "agent-interface-wslc-s30-a57146d1c900",
    "one_session_start": stages.count("session_started") == 1,
    "one_exact_name_preflight": stages.count("exact_name_preflight") == 1 and preflight.get("filter") == "name=" + prereg["container_name"],
    "preflight_path_not_found": preflight.get("exit") == 1 and preflight.get("stdout", "") == "" and "ERROR_PATH_NOT_FOUND" in preflight.get("stderr", ""),
    "no_container_created": "container_created" not in stages and cleanup.get("cid") is None,
    "no_image_pull": "image_pull_complete" not in stages and cleanup.get("pulled") is False,
    "task_never_started": "trial-started.txt" not in {p.name for p in (external / "output").iterdir()} and not (external / "output" / "result.json").exists(),
    "session_terminated": stages.count("session_terminated") == 1 and cleanup.get("started") is True and cleanup.get("terminated") is True,
    "no_container_cleanup_needed": cleanup.get("deleted") is False and cleanup.get("imageDeleted") is False,
    "no_retry": stages.count("session_started") == 1 and stages.count("exact_name_preflight") == 1,
    "scoped_preflight_only_no_global_inventory_or_docker": 'new[]{"--session",sessionName,"container","list","--all","--filter","name="+containerName' in host_source and '"session","list"' not in host_source and '"image","ls"' not in host_source and "docker.exe" not in host_source.lower(),
    "session_storage_empty": storage.exists() and not any(storage.iterdir()),
}
result = {
    "schema": "agent-interface/wslc-s30-independent-setup-audit-v1",
    "attempt_id": attempt,
    "classification": "HOLD_PRETRIAL_EXACT_NAME_PREFLIGHT_PATH_NOT_FOUND",
    "audited_without_runtime_import": True,
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "failed": [key for key, value in checks.items() if not value],
    "observations": {
        "formal_invocation_exit_code": 1,
        "task_input_started": False,
        "container_created": False,
        "image_pulled": False,
        "session_terminated": cleanup.get("terminated"),
        "session_storage_empty": not any(storage.iterdir()),
        "failure": "wslc.exe exact-name preflight returned ERROR_PATH_NOT_FOUND",
    },
}
(root / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"classification": result["classification"], "passed": result["passed"], "total": result["total"], "failed": result["failed"]}, sort_keys=True))
