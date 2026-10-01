"""Single-use, bounded Windows host launcher for the formal Docker allocation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


IMAGE = "python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
ENGINE_NAME = "cactus_needle-3.0.1-py3-none-manylinux2014_x86_64.whl"
CLIENT_NAME = "cactus_needle-3.0.1-py3-none-any.whl"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--client-wheelhouse", type=Path, required=True)
    parser.add_argument("--engine-wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--freeze-sha256", required=True)
    args = parser.parse_args()

    study = args.study.resolve(strict=True)
    model = args.model.resolve(strict=True)
    wheelhouse = args.client_wheelhouse.resolve(strict=True)
    engine = args.engine_wheel.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    if digest(study / "FREEZE.json") != args.freeze_sha256.lower():
        raise SystemExit("STOP_FREEZE_DIGEST_MISMATCH")
    freeze = json.loads((study / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["source_sha256"].items():
        if digest(study / name) != expected:
            raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH:{name}")
    for path, expected in (
        (model, freeze["candidate"]["weights_sha256"]),
        (wheelhouse / CLIENT_NAME, freeze["candidate"]["client_wheel_sha256"]),
        (engine, freeze["candidate"]["engine_wheel_sha256"]),
    ):
        if digest(path) != expected:
            raise SystemExit(f"STOP_ARTIFACT_HASH_MISMATCH:{path.name}")
    for line in (study / "CLIENT_WHEELS.sha256").read_text(encoding="utf-8").splitlines():
        expected, filename = line.split(maxsplit=1)
        artifact = wheelhouse / filename.strip()
        if not artifact.is_file() or digest(artifact) != expected:
            raise SystemExit(f"STOP_CLIENT_DEPENDENCY_HASH_MISMATCH:{filename.strip()}")
    output.mkdir(parents=True, exist_ok=False)
    cidfile = output / "container.cid"
    command = [
        "docker", "run", "--rm", "--cidfile", str(cidfile),
        "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,exec,size=512m",
        "--memory", "2g", "--cpus", "2", "--pids-limit", "64", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--mount", f"type=bind,source={model},target=/model/needle3.cact,readonly",
        "--mount", f"type=bind,source={wheelhouse},target=/wheels,readonly",
        "--mount", f"type=bind,source={engine},target=/{ENGINE_NAME},readonly",
        "--mount", f"type=bind,source={study},target=/study,readonly",
        "--mount", f"type=bind,source={output},target=/output",
        "-e", "HF_HUB_OFFLINE=1", "-e", "NEEDLE_TELEMETRY=0",
        "-e", "NEEDLE3_LIB_PATH=/tmp/engine/needle/libneedle3.so",
        "-e", "PYTHONPATH=/tmp/client:/tmp/engine", "-e", "CUDA_VISIBLE_DEVICES=-1",
        IMAGE, "/bin/sh", "-c",
        "python -m pip install --no-index --find-links=/wheels --target /tmp/client cactus-needle==3.0.1 "
        ">/output/pip-client.log 2>&1 && "
        f"python -m pip install --no-index --no-deps --target /tmp/engine /{ENGINE_NAME} "
        ">/output/pip-engine.log 2>&1 && cd /study && "
        "python runner.py --freeze-sha256 " + args.freeze_sha256.lower() +
        " --model /model/needle3.cact --client-wheel /wheels/" + CLIENT_NAME +
        " --engine-wheel /" + ENGINE_NAME + " --output /output",
    ]
    record = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": 180,
        "image": IMAGE,
        "command": command,
        "model_sha256": digest(model),
        "client_wheel_sha256": digest(wheelhouse / CLIENT_NAME),
        "engine_wheel_sha256": digest(engine),
    }
    (output / "host-invocation.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    status, stdout, stderr = 2, b"", b""
    try:
        completed = subprocess.run(command, capture_output=True, timeout=180, check=False)
        status, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        if isinstance(stdout, str):
            stdout = stdout.encode()
        if isinstance(stderr, str):
            stderr = stderr.encode()
        if cidfile.is_file():
            container_id = cidfile.read_text(encoding="ascii").strip()
            if container_id:
                stopped = subprocess.run(["docker", "stop", "--time", "2", container_id], capture_output=True, check=False)
                stderr += b"\nTIMEOUT_STOP " + stopped.stdout + stopped.stderr
        stderr += b"\nSTOP_HOST_TIMEOUT_180_SECONDS\n"
    (output / "docker.stdout.log").write_bytes(stdout)
    (output / "docker.stderr.log").write_bytes(stderr)
    record.update({"finished_at_utc": datetime.now(timezone.utc).isoformat(), "exit_code": status})
    (output / "host-invocation.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
