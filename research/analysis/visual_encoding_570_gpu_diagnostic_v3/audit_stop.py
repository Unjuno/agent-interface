from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STOP_PATH = Path(__file__).with_name("STOP.json")
EXPECTED_ERROR = "failed to discover GPU vendor from CDI: no known GPU vendor found"


def audit(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != "visual-encoding-570-gpu-preflight-stop-v1":
        errors.append("schema")
    if record.get("disposition") != "STOP_GPU_OFFLOAD_UNAVAILABLE":
        errors.append("disposition")
    if record.get("stage") != "docker_gpu_runtime_preflight_before_ollama_or_model_launch":
        errors.append("stage")
    env = record.get("environment", {})
    if env.get("docker_server_os") != "linux" or env.get("docker_server_arch") != "arm64":
        errors.append("docker_platform")
    if "runc" not in env.get("docker_runtimes", []):
        errors.append("runtime_inventory")
    if env.get("nvidia_smi_available") is not False:
        errors.append("nvidia_tool_observation")
    probe = record.get("probe", {})
    if probe.get("exit_code") != 125:
        errors.append("probe_exit")
    if "--gpus all" not in probe.get("command", ""):
        errors.append("gpu_request")
    if EXPECTED_ERROR not in probe.get("stderr", ""):
        errors.append("raw_daemon_error")
    if probe.get("stdout") != "":
        errors.append("unexpected_container_stdout")
    if record.get("formal_model_requests") != 0:
        errors.append("model_request_count")
    if record.get("ollama_image_pulled") is not False:
        errors.append("ollama_image_pull")
    if record.get("formal_allocations_run") != 0 or record.get("retry_count") != 0:
        errors.append("formal_or_retry_count")
    limits = record.get("limits", [])
    if not any("not a model localization failure" in item for item in limits):
        errors.append("scope_limit")
    return errors


def main() -> int:
    record = json.loads(STOP_PATH.read_text(encoding="utf-8"))
    errors = audit(record)
    print(f"disposition={record.get('disposition')} checks=14 errors={len(errors)}")
    for error in errors:
        print(f"error={error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
