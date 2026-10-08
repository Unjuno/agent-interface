from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


IMAGE = "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args, timeout=30):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codex-exe", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ipc", required=True)
    parser.add_argument("--container-name", required=True)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    study = Path(__file__).resolve().parent
    repo = study.parents[2]
    output = Path(args.output).resolve()
    ipc = Path(args.ipc).resolve()
    formal = output / "formal01"
    errors = []

    manifest_path = study / "SOURCE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative, expected in manifest["source_sha256"].items():
        path = repo / relative
        if not path.is_file() or digest(path) != expected:
            errors.append(f"source hash mismatch: {relative}")

    codex = Path(args.codex_exe).resolve()
    if not codex.is_file() or digest(codex) != manifest["codex_exe_sha256"]:
        errors.append("Codex executable missing or hash mismatch")
    version = run([str(codex), "--version"])
    if version.returncode or version.stdout.strip() != manifest["codex_cli_version"]:
        errors.append("Codex CLI version mismatch")
    login = run([str(codex), "login", "status"])
    login_text = login.stdout + "\n" + login.stderr
    if login.returncode or "Logged in using ChatGPT" not in login_text:
        errors.append("Codex login unavailable")

    context = run(["docker", "context", "show"])
    engine = run(["docker", "version", "--format", "{{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}"])
    image = run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"])
    expected_image_line = manifest["image_id"] + " " + manifest["image_platform"]
    if context.returncode or context.stdout.strip() != manifest["docker_context"]:
        errors.append("Docker context mismatch")
    if engine.returncode or engine.stdout.strip() != manifest["docker_engine"]:
        errors.append("Docker engine mismatch")
    if image.returncode or image.stdout.strip() != expected_image_line:
        errors.append("Docker image unavailable or identity mismatch")
    names = {p.name for p in output.iterdir()} if output.exists() else set()
    expected_names = {"environment.json", "preflight.json"}
    if formal.exists() or any(ipc.iterdir()):
        errors.append("formal output or IPC path is not empty")
    if args.preflight_only and names:
        errors.append("preflight output path was not empty at preflight start")
    if not args.preflight_only and names != expected_names:
        errors.append("formal start requires only the retained pre-call receipts")
    if not args.preflight_only and names == expected_names:
        try:
            old_preflight = json.loads((output / "preflight.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            old_preflight = {}
        if old_preflight.get("status") != "PASS_PRECALL_PREFLIGHT" or old_preflight.get("formal_model_call_started") is not False:
            errors.append("prior pre-call gate is absent or did not pass")
    existing = run(["docker", "ps", "-a", "--filter", "name=^/" + args.container_name + "$", "--format", "{{.Names}}"])
    if existing.stdout.strip():
        errors.append("container name already exists")

    environment = {
        "docker_context": context.stdout.strip(),
        "docker_engine": engine.stdout.strip(),
        "docker_image": IMAGE,
        "image_id": manifest["image_id"] if not image.returncode else image.stdout.strip(),
        "image_platform": manifest["image_platform"],
        "codex_cli_version": version.stdout.strip(),
        "codex_exe_sha256": digest(codex) if codex.is_file() else None,
        "codex_login_status": login_text.strip() if login.returncode == 0 else "unavailable",
        "container_name": args.container_name,
        "source_sha256": {p: digest(repo / p) for p in manifest["source_sha256"] if (repo / p).is_file()},
        "preflight_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "preflight_model_calls": 0,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "environment.json").write_text(json.dumps(environment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    preflight = {"status": "PASS_PRECALL_PREFLIGHT" if not errors else "STOP_PREFLIGHT", "errors": errors,
                 "formal_model_call_started": False, "output_formal01_absent": not formal.exists(),
                 "ipc_empty": not any(ipc.iterdir())}
    (output / "preflight.json").write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if errors:
        print(json.dumps(preflight))
        return 1
    if args.preflight_only:
        print(json.dumps(preflight))
        return 0

    docker_args = [
        "docker", "run", "--name", args.container_name,
        "--network", "none", "--read-only", "--cpus", "1.0",
        "--memory", "512m", "--pids-limit", "64",
        "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "--mount", f"type=bind,source={repo},target=/repo,readonly",
        "--mount", f"type=bind,source={output},target=/output",
        "--mount", f"type=bind,source={ipc},target=/ipc",
        "--workdir", "/repo",
        "--env", "HOST_MODEL_IPC_DIR=/ipc",
        "--env", "HOST_MODEL_IPC_TIMEOUT_S=120",
        "--env", "PYTHONDONTWRITEBYTECODE=1",
        IMAGE,
        "python", "/repo/research/live_control/issue_2849_runner_aux_event_v2_v1/event_accounting.py",
        "python", "/usr/bin/codex",
        "/repo/research/integration/issue_4710_docker_desktop_current_main_preflight_v1/prompt.txt",
        "/repo/.empty-workspace", "/output/formal01", "compiled", "-",
        "/repo/research/live_control/compiled_form_grounding_responder_v1.txt",
        "/repo/research/live_control/compiled_form_grounding_schema_v1.json",
    ]
    env = os.environ.copy()
    env["CODEX_EXE"] = str(codex)
    env["HOST_MODEL_BROKER_TIMEOUT_S"] = "90"
    broker_log = output / "broker-process"
    broker_log.mkdir()
    broker_cmd = [sys.executable, str(repo / "runtime/host_model_ipc_broker_v1.py"),
                  "--ipc", str(ipc), "--repo", str(repo), "--once"]
    with (broker_log / "stdout.txt").open("w", encoding="utf-8") as stdout, (broker_log / "stderr.txt").open("w", encoding="utf-8") as stderr:
        broker = subprocess.Popen(broker_cmd, env=env, stdout=stdout, stderr=stderr)
        result = None
        try:
            result = run(docker_args, timeout=180)
        except subprocess.TimeoutExpired as exc:
            result = subprocess.CompletedProcess(docker_args, 124, exc.stdout or "", exc.stderr or "docker-run-timeout")
            run(["docker", "stop", "--time", "2", args.container_name], timeout=10)
        try:
            broker_rc = broker.wait(timeout=15)
        except subprocess.TimeoutExpired:
            broker.terminate()
            try:
                broker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                broker.kill()
                broker.wait()
            broker_rc = None

    inspect = run(["docker", "inspect", args.container_name], timeout=15)
    inspect_data = None
    if inspect.returncode == 0:
        raw = json.loads(inspect.stdout)[0]
        inspect_data = {
            "Id": raw.get("Id"),
            "Image": raw.get("Image"),
            "ConfigImage": raw.get("Config", {}).get("Image"),
            "State": {key: raw.get("State", {}).get(key) for key in ("Status", "ExitCode", "OOMKilled", "Error")},
            "NetworkMode": raw.get("HostConfig", {}).get("NetworkMode"),
            "ReadonlyRootfs": raw.get("HostConfig", {}).get("ReadonlyRootfs"),
            "CapDrop": raw.get("HostConfig", {}).get("CapDrop"),
            "SecurityOpt": raw.get("HostConfig", {}).get("SecurityOpt"),
            "PidsLimit": raw.get("HostConfig", {}).get("PidsLimit"),
            "Memory": raw.get("HostConfig", {}).get("Memory"),
            "NanoCpus": raw.get("HostConfig", {}).get("NanoCpus"),
            "Mounts": [{"Target": m.get("Destination"), "RW": m.get("RW"), "Type": m.get("Type")} for m in raw.get("Mounts", [])],
        }
    cleanup = run(["docker", "rm", args.container_name], timeout=15)
    (output / "docker-stdout.txt").write_text(result.stdout or "", encoding="utf-8")
    (output / "docker-stderr.txt").write_text(result.stderr or "", encoding="utf-8")
    if inspect_data is not None:
        (output / "container-inspect.json").write_text(json.dumps(inspect_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    broker_receipts = sorted(ipc.glob("*.broker.json"))
    broker_receipt = json.loads(broker_receipts[0].read_text(encoding="utf-8")) if len(broker_receipts) == 1 else None
    if len(broker_receipts) != 1:
        # A started request without an attributable broker receipt is not safe to retry.
        call_may_have_started = bool(list(ipc.glob("*.request.json")))
    else:
        call_may_have_started = broker_receipt.get("returncode") is not None or broker_receipt.get("error_class") == "TimeoutExpired"
    request_receipts = sorted(ipc.glob("*.request.json"))
    response_receipts = sorted(ipc.glob("*.response.jsonl"))
    launcher_result = {
        "container_exit_code": result.returncode,
        "docker_network": "none",
        "read_only_root": True,
        "source_read_only": True,
        "output_and_ipc_are_only_writable_host_mounts": True,
        "image_id": environment["image_id"],
        "image_platform": environment["image_platform"],
        "broker_process_exit_code": broker_rc,
        "broker_receipt_present": broker_receipt is not None,
        "request_count": len(request_receipts),
        "response_count": len(response_receipts),
        "broker_receipt_count": len(broker_receipts),
        "model_call_may_have_started": call_may_have_started,
        "docker_cleanup_exit_code": cleanup.returncode,
        "docker_command_redacted": [arg.replace(str(repo), "<STUDY_ROOT>").replace(str(output), "<OUTPUT>").replace(str(ipc), "<IPC>").replace(str(codex), "<CODEX_EXE>") for arg in docker_args],
        "container_inspect": inspect_data,
    }
    (output / "launcher-result.json").write_text(json.dumps(launcher_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"container_exit_code": result.returncode, "broker_process_exit_code": broker_rc,
                      "broker_receipt_present": broker_receipt is not None, "model_call_may_have_started": launcher_result["model_call_may_have_started"]}))
    return 0 if result.returncode == 0 and broker_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
