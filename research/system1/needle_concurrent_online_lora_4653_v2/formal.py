#!/usr/bin/env python3
"""Single-shot host wrapper for construction checks, trainer, and raw-only audit."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

IMAGE = "needle-pilot05:local"
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run_logged(name, cmd, out, timeout):
    start = time.time()
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        code, stdout, stderr = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 124, exc.stdout or "", exc.stderr or "timeout"
    (out / f"{name}.stdout.txt").write_text(stdout, encoding="utf-8")
    (out / f"{name}.stderr.txt").write_text(stderr, encoding="utf-8")
    return {"name": name, "argv": cmd, "exit_code": code, "start_unix": start,
            "duration_seconds": time.time() - start, "stdout_sha256": sha(out / f"{name}.stdout.txt"),
            "stderr_sha256": sha(out / f"{name}.stderr.txt")}


def docker_prefix(src, out):
    return ["docker", "run", "--rm", "--network", "none", "--read-only", "--cpus=1",
            "--memory=2g", "--pids-limit=64", "--security-opt=no-new-privileges",
            "--entrypoint", "python", "--workdir", "/src",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
            "--mount", f"type=bind,src={src},dst=/src,readonly",
            "--mount", f"type=bind,src={out},dst=/out", IMAGE_ID]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--formal", action="store_true", help="execute the single frozen formal allocation after construction tests")
    args = p.parse_args()
    src, out = Path(args.source).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    freeze = json.loads((src / "FREEZE.json").read_text(encoding="utf-8"))
    actual = {name: sha(src / name) for name in freeze["source_sha256"]}
    if actual != freeze["source_sha256"]:
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    if sha(src / "FREEZE.json") != (src / "FREEZE.sha256").read_text(encoding="ascii").strip():
        raise SystemExit("STOP_FREEZE_HASH_MISMATCH")
    image = subprocess.run(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
                           capture_output=True, text=True, check=False)
    if image.returncode or image.stdout.strip() != IMAGE_ID:
        raise SystemExit("STOP_PINNED_IMAGE_UNAVAILABLE_OR_MISMATCH")
    engine = subprocess.run(["docker", "version", "--format", "{{.Client.Version}} / {{.Server.Version}}"],
                            capture_output=True, text=True, check=False)
    if engine.returncode:
        raise SystemExit("STOP_DOCKER_ENGINE_UNAVAILABLE")
    test_out = out / "construction"
    test_out.mkdir(exist_ok=True)
    base = docker_prefix(src, out)
    started = time.time()
    construction = run_logged("construction", base + ["-m", "unittest", "-v", "test_construction"], out, 120)
    construction["start_unix"] = started
    if construction["exit_code"] != 0:
        (out / "FORMAL_INVOCATION.json").write_text(json.dumps({"status": "STOP_CONSTRUCTION_TESTS",
            "construction": construction, "engine": engine.stdout.strip(), "image_id": IMAGE_ID}, indent=2)+"\n", encoding="utf-8")
        raise SystemExit(construction["exit_code"])
    if not args.formal:
        print(json.dumps({"construction": construction, "engine": engine.stdout.strip(), "image_id": IMAGE_ID}, sort_keys=True))
        return
    invocation = {"status": "RUNNING", "source": str(src), "source_sha256": actual,
        "freeze_sha256": sha(src / "FREEZE.json"), "image": IMAGE, "image_id": IMAGE_ID,
        "docker_engine": engine.stdout.strip(), "host_python": sys.version,
        "host_platform": platform.platform(), "construction": construction,
        "formal_started_unix": time.time(), "host_argv": sys.argv, "retry_count": 0}
    (out / "FORMAL_INVOCATION.json").write_text(json.dumps(invocation, indent=2)+"\n", encoding="utf-8")
    trainer = run_logged("trainer", base + ["/src/runner.py", "--out", "/out/training"], out, 900)
    auditor = run_logged("auditor", base + ["/src/audit.py", "--raw", "/out/training", "--out", "/out/AUDIT.json"], out, 300)
    completion = {"status": "COMPLETE" if trainer["exit_code"] == 0 and auditor["exit_code"] == 0 else "FORMAL_PROCESS_FAILURE",
        "trainer": trainer, "auditor": auditor, "completed_unix": time.time(), "retry_count": 0}
    (out / "FORMAL_COMPLETION.json").write_text(json.dumps(completion, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(completion, sort_keys=True), flush=True)
    if trainer["exit_code"] or auditor["exit_code"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
