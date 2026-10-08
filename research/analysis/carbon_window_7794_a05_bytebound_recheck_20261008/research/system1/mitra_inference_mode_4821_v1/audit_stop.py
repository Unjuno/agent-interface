#!/usr/bin/env python3
"""Independent posthoc verifier for the immutable #4935 pre-model STOP."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    stop_path = ROOT / "formal-01" / "STOP.json"
    invocation_path = ROOT / "host-evidence-01" / "INVOCATION.json"
    stderr_path = ROOT / "host-evidence-01" / "runner.stderr.txt"
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    invocation = json.loads(invocation_path.read_text(encoding="utf-8"))
    stderr = stderr_path.read_text(encoding="utf-8")
    errors = []
    if stop.get("schema") != "mitra-inference-mode-stop-4935-v1" or stop.get("issue") != 4935:
        errors.append("STOP_IDENTITY")
    if stop.get("allocation") != freeze.get("allocation") or stop.get("stage") != "context_setup":
        errors.append("STOP_STAGE_OR_ALLOCATION")
    if stop.get("exception_type") != "HFValidationError" or "/model/model.safetensors" not in stop.get("message", ""):
        errors.append("EXPECTED_HF_PATH_ERROR_MISSING")
    if stop.get("optimizer_step_calls") != 0 or "No such file" in stderr:
        errors.append("OPTIMIZER_OR_ALTERNATE_FAILURE")
    if invocation.get("exit_code") != 1 or invocation.get("image_id", "").split()[0] != freeze.get("execution", {}).get("image_id"):
        errors.append("INVOCATION_IDENTITY")
    command = invocation.get("command", [])
    if not all(x in command for x in ("--gpus", "all", "--network", "none", "--read-only")):
        errors.append("FORMAL_COMMAND_GATES")
    if "HFValidationError" not in stderr or "hf_hub_download(repo_id=path_or_repo_id, filename=filename)" not in stderr:
        errors.append("STDERR_CAUSAL_TRACE")
    if (ROOT / "formal-01" / "RAW.json").exists():
        errors.append("RAW_SHOULD_NOT_EXIST")
    if (ROOT / "audit-01" / "AUDIT.json").exists():
        errors.append("RESULT_AUDIT_SHOULD_NOT_EXIST")
    for name, expected in freeze.get("source_sha256", {}).items():
        if sha(ROOT / name) != expected:
            errors.append("SOURCE_HASH:" + name)
    result = {"schema": "mitra-inference-mode-stop-audit-4935-v1", "issue": 4935,
        "allocation": freeze["allocation"], "status": "PASS_STOP_AUDITED" if not errors else "HOLD_STOP_AUDIT",
        "errors": errors, "stop_sha256": sha(stop_path), "invocation_sha256": sha(invocation_path),
        "stderr_sha256": sha(stderr_path), "freeze_sha256": sha(ROOT / "FREEZE.json"),
        "formal_gpu_requested_invocations": 1, "successful_model_loads": 0,
        "inference_calls": 0, "optimizer_steps": stop.get("optimizer_step_calls"),
        "cause": "hf_model received the model.safetensors file path; AutoGluon treated it as a Hub repo ID before loading the checkpoint"}
    (ROOT / "formal-01" / "STOP_AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
