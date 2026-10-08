#!/usr/bin/env python3
"""One candidate or audit Docker invocation on an isolated Actions runner."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


IMAGE = "python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a"
ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "research/analysis/surrogate_endpoint_gate_5686_t0_20261001"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def invoke(label, command, out):
    started = stamp()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (out / (label + ".stdout")).write_bytes(result.stdout)
    (out / (label + ".stderr")).write_bytes(result.stderr)
    return {"label": label, "command": command, "started_utc": started,
            "finished_utc": stamp(), "exit_code": result.returncode,
            "stdout_sha256": sha_bytes(result.stdout), "stderr_sha256": sha_bytes(result.stderr)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("candidate", "audit"))
    parser.add_argument("--input-dir")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        print("STOP_OUTPUT_NOT_EMPTY", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    result = {"allocation": "SURROGATE-ENDPOINT-GATE-5686-T0-GHA-20261001-04",
              "role": args.role, "image_ref": IMAGE, "expected_platform": "linux/amd64",
              "host_python": sys.version, "host_platform": platform.platform(),
              "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
              "started_utc": stamp(), "image_pull": None, "image_inspect": None, "container": None}
    try:
        result["docker_server"] = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}|{{.OSType}}/{{.Architecture}}"],
            capture_output=True, text=True, check=True).stdout.strip()
        pull = invoke("image-pull", ["docker", "pull", IMAGE], out)
        result["image_pull"] = pull
        if pull["exit_code"]:
            raise RuntimeError("pinned image pull failed; no candidate/audit container launched")
        inspect = subprocess.run(["docker", "image", "inspect", "--format",
                                  "{{.Id}}|{{.Os}}/{{.Architecture}}|{{json .RepoDigests}}", IMAGE],
                                 capture_output=True, text=True, check=True)
        result["image_inspect"] = inspect.stdout.strip()
        fields = inspect.stdout.strip().split("|", 2)
        if len(fields) != 3 or fields[1] != "linux/amd64" or IMAGE.split("@", 1)[1] not in fields[2]:
            raise RuntimeError("pinned image digest/platform mismatch")
        result["image_id"] = fields[0]
        source_mounts = []
        command = ["python3"]
        name = "agent-interface-5686-t0-" + args.role + "-" + os.environ.get("GITHUB_RUN_ID", "run")
        if args.role == "candidate":
            source_mounts = [(PACKAGE / "candidate.py", "/input/candidate.py"),
                             (PACKAGE / "fixtures.json", "/input/fixtures.json"),
                             (out, "/out")]
            container_code = ("import json,os,platform,sys; "
                              "print(json.dumps({'runtime_python':sys.version,'runtime_platform':platform.platform()},sort_keys=True),flush=True); "
                              "os.execv(sys.executable,[sys.executable,'/input/candidate.py','--input','/input/fixtures.json','--output','/out/candidate.jsonl'])")
            command += ["-c", container_code]
        else:
            input_dir = Path(args.input_dir).resolve()
            raw = input_dir / "candidate.jsonl"
            if not raw.is_file():
                raise RuntimeError("candidate artifact missing; auditor not launched")
            source_mounts = [(PACKAGE / "audit.py", "/input/audit.py"),
                             (PACKAGE / "fixtures.json", "/input/fixtures.json"),
                             (raw, "/input/candidate.jsonl"), (out, "/out")]
            container_code = ("import json,os,platform,sys; "
                              "print(json.dumps({'runtime_python':sys.version,'runtime_platform':platform.platform()},sort_keys=True),flush=True); "
                              "os.execv(sys.executable,[sys.executable,'/input/audit.py','--input','/input/candidate.jsonl','--fixtures','/input/fixtures.json','--output','/out/audit.json'])")
            command += ["-c", container_code]
        docker = ["docker", "run", "--pull=never", "--rm", "--name", name,
                  "--cidfile", str(out / "container.cid"), "--platform", "linux/amd64",
                  "--user", f"{os.getuid()}:{os.getgid()}",
                  "--network", "none", "--read-only", "--cpus", "1", "--memory", "536870912",
                  "--pids-limit", "64", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                  "--tmpfs", f"/tmp:rw,nosuid,nodev,noexec,size=16777216,uid={os.getuid()},gid={os.getgid()}",
                  "-e", "PYTHONDONTWRITEBYTECODE=1"]
        for source, target in source_mounts:
            docker += ["--mount", f"type=bind,source={source},target={target},readonly" if target != "/out" else f"type=bind,source={source},target={target}"]
        docker += [IMAGE, *command]
        container = invoke("container", docker, out)
        result["container"] = container
    except Exception as exc:
        result["runner_error"] = f"{type(exc).__name__}: {exc}"
    result["finished_utc"] = stamp()
    for file in sorted(out.iterdir()):
        if file.is_file() and file.name != "execution.json":
            result.setdefault("artifact_sha256", {})[file.name] = sha_bytes(file.read_bytes())
    (out / "execution.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"role": args.role, "container_exit": (result["container"] or {}).get("exit_code"),
                      "runner_error": result.get("runner_error")}, sort_keys=True))
    if result.get("runner_error"):
        return 2
    return (result["container"] or {}).get("exit_code", 2)


if __name__ == "__main__":
    raise SystemExit(main())
