import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"
conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8-sig"))
wrapper = json.loads((RUN / "api-run-wrapper.json").read_text(encoding="utf-8-sig"))
events = [
    json.loads(line)
    for line in (RUN / "api-run.stdout.jsonl").read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
]
stages = {event["stage"]: event["details"] for event in events if event["stage"] != "pull_progress"}
created = stages["container_created"]
exited = stages["container_exited"]
probe = json.loads(exited["outputText"].strip())
runner_failure = stages.get("failure")
session_storage = Path(conditions["session_storage_path"])
storage_cleanup = json.loads((RUN / "storage-retained.json").read_text(encoding="utf-8-sig"))

criteria = {
    "prerequisites_empty": stages["prerequisites"]["missing"] == [],
    "session_started": "session_started" in stages,
    "image_pull_complete": "image_pull_complete" in stages,
    "container_id_full_sha256": len(created["containerId"]) == 64,
    "container_network_none": created["networkingMode"] == "None",
    "mount_readonly": created["volumeReadOnly"] is True,
    "probe_marker": probe["probe"] == "PASS",
    "sentinel_sha256_matches": probe["bytes_sha256"] == conditions["sentinel_sha256"],
    "write_rejected_ero_fs": probe["write_rejected_errno"] == "EROFS",
    "container_process_exit_zero": exited["processExit"] == 0,
    "container_deleted": "container_deleted" in stages,
    "image_deleted": "image_deleted" in stages,
    "dedicated_session_terminated": "session_terminated" in stages,
    "session_storage_removed": not session_storage.exists(),
    "wrapper_false_negative_is_known_matcher": bool(
        runner_failure
        and "expected PASS marker" in runner_failure["message"]
        and wrapper["exit_code"] == 1
        and not wrapper["timed_out"]
    ),
}
pass_without_wrapper_false_negative = all(
    value
    for key, value in criteria.items()
    if key not in {"wrapper_false_negative_is_known_matcher", "session_storage_removed"}
)
storage_exists_after_termination = session_storage.exists()
classification = (
    "RUNTIME_PASS_WITH_RUNNER_FALSE_NEGATIVE_AND_CLEANUP_HOLD"
    if pass_without_wrapper_false_negative
    and criteria["wrapper_false_negative_is_known_matcher"]
    and not criteria["session_storage_removed"]
    else "PASS"
    if pass_without_wrapper_false_negative
    and criteria["wrapper_false_negative_is_known_matcher"]
    and criteria["session_storage_removed"]
    else "HOLD_UNKNOWN"
)
audit = {
    "schema": "wslc-local-runtime-api-smoke-s04-audit-v1",
    "classification": classification,
    "criteria": criteria,
    "probe_stdout_json": probe,
    "container_id": created["containerId"],
    "container_configuration": created,
    "runner_failure": runner_failure,
    "wrapper_exit_code": wrapper["exit_code"],
    "session_storage_path": str(session_storage),
    "session_storage_exists_after_termination": storage_exists_after_termination,
    "storage_cleanup": storage_cleanup,
    "pull_progress_event_count": sum(event["stage"] == "pull_progress" for event in events),
}
(RUN / "runtime-audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
