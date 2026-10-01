#!/usr/bin/env python3
"""Run exactly one candidate or auditor in the frozen isolated Docker image."""
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
PACKAGE = ROOT / "research/analysis/surrogate_selection_feedback_5686_t2_20261001"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def captured(label, command, out):
    started = now()
    done = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (out / (label + ".stdout")).write_bytes(done.stdout)
    (out / (label + ".stderr")).write_bytes(done.stderr)
    return {"label": label, "command": command, "started_utc": started, "finished_utc": now(),
            "exit_code": done.returncode, "stdout_sha256": digest(done.stdout), "stderr_sha256": digest(done.stderr)}


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
    uid, gid = os.getuid(), os.getgid()
    report = {"allocation": "SURROGATE-SELECTION-5686-T2-GHA-20261001-01", "role": args.role,
              "image_ref": IMAGE, "expected_platform": "linux/amd64", "host_python": sys.version,
              "host_platform": platform.platform(), "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
              "started_utc": now(), "image_pull": None, "image_inspect": None, "container": None}
    try:
        report["docker_server"] = subprocess.run(["docker", "info", "--format", "{{.ServerVersion}}|{{.OSType}}/{{.Architecture}}"], capture_output=True, text=True, check=True).stdout.strip()
        report["image_pull"] = captured("image-pull", ["docker", "pull", IMAGE], out)
        if report["image_pull"]["exit_code"]:
            raise RuntimeError("pinned image pull failed; no experiment container launched")
        inspected = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}|{{.Os}}/{{.Architecture}}|{{json .RepoDigests}}", IMAGE], capture_output=True, text=True, check=True).stdout.strip()
        report["image_inspect"] = inspected
        fields = inspected.split("|", 2)
        if len(fields) != 3 or fields[1] != "linux/amd64" or IMAGE.split("@", 1)[1] not in fields[2]:
            raise RuntimeError("pinned image digest/platform mismatch")
        report["image_id"] = fields[0]
        mounts = [(PACKAGE / "fixtures.json", "/input/fixtures.json")]
        if args.role == "candidate":
            mounts.append((PACKAGE / "candidate.py", "/input/candidate.py"))
            snippet = "import json,os,sys; print(json.dumps({'runtime_python':sys.version},sort_keys=True),flush=True); os.execv(sys.executable,[sys.executable,'/input/candidate.py','--input','/input/fixtures.json','--output','/out/candidate.jsonl'])"
        else:
            source = Path(args.input_dir).resolve() / "candidate.jsonl"
            if not source.is_file():
                raise RuntimeError("candidate artifact missing; auditor not launched")
            mounts.extend([(PACKAGE / "audit.py", "/input/audit.py"), (source, "/input/candidate.jsonl")])
            snippet = "import json,os,sys; print(json.dumps({'runtime_python':sys.version},sort_keys=True),flush=True); os.execv(sys.executable,[sys.executable,'/input/audit.py','--input','/input/candidate.jsonl','--fixtures','/input/fixtures.json','--output','/out/audit.json'])"
        run = ["docker", "run", "--pull=never", "--rm", "--name", "agent-interface-5686-t2-" + args.role + "-" + os.environ.get("GITHUB_RUN_ID", "run"),
               "--cidfile", str(out / "container.cid"), "--platform", "linux/amd64", "--user", f"{uid}:{gid}",
               "--network", "none", "--read-only", "--cpus", "1", "--memory", "536870912", "--pids-limit", "64",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "--tmpfs", f"/tmp:rw,nosuid,nodev,noexec,size=16777216,uid={uid},gid={gid}",
               "-e", "PYTHONDONTWRITEBYTECODE=1"]
        for host, target in mounts:
            run.extend(["--mount", f"type=bind,source={host},target={target},readonly"])
        run += ["--mount", f"type=bind,source={out},target=/out", IMAGE, "python3", "-c", snippet]
        report["container"] = captured("container", run, out)
    except Exception as exc:
        report["runner_error"] = f"{type(exc).__name__}: {exc}"
    report["finished_utc"] = now()
    report["artifact_sha256"] = {f.name: digest(f.read_bytes()) for f in sorted(out.iterdir()) if f.is_file() and f.name != "execution.json"}
    (out / "execution.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"role": args.role, "container_exit": (report["container"] or {}).get("exit_code"), "runner_error": report.get("runner_error")}, sort_keys=True))
    if report.get("runner_error"):
        return 2
    return (report["container"] or {}).get("exit_code", 2)


if __name__ == "__main__":
    raise SystemExit(main())
