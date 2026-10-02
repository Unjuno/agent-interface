"""One-shot OrbStack runner for the #6590 training-parity construction gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def runtime_config(freeze: dict) -> dict:
    runtime = freeze["runtime"]
    for key in ("docker_context", "image_id", "platform", "construction_container_name"):
        if not runtime.get(key):
            raise ValueError(f"STOP_RUNTIME_FREEZE_MISSING:{key}")
    return runtime


def run(source: Path, output: Path) -> int:
    source = source.resolve()
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_ABSENT")
    output.mkdir(parents=True, exist_ok=True)
    freeze = None
    stage = "freeze_readback"
    try:
        freeze_path = source / "FREEZE.json"
        freeze_sha = (source / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
        if sha(freeze_path) != freeze_sha:
            raise ValueError("STOP_FREEZE_SIDECAR_MISMATCH")
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        runtime = runtime_config(freeze)
        stage = "source_readback"
        for rel, expected in freeze["source_sha256"].items():
            if sha(source / rel) != expected:
                raise ValueError(f"STOP_SOURCE_HASH_MISMATCH:{rel}")
        root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=source, text=True).strip())
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
        parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=source, text=True).strip()
        if parent != freeze["source_commit"]:
            raise ValueError(f"STOP_SOURCE_COMMIT_MISMATCH:{parent}")
        changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=source, text=True).splitlines()
        expected_freeze_paths = sorted([str(freeze_path.relative_to(root)), str((source / "FREEZE.sha256").relative_to(root))])
        if sorted(changed) != expected_freeze_paths:
            raise ValueError(f"STOP_FREEZE_COMMIT_SCOPE_MISMATCH:{changed}")
        if subprocess.check_output(["git", "status", "--porcelain"], cwd=source, text=True).strip():
            raise ValueError("STOP_DIRTY_WORKTREE")
        latest_main = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], cwd=source, text=True).split()[0]
        frozen_main = freeze["main_sha"]
        if subprocess.run(["git", "merge-base", "--is-ancestor", frozen_main, latest_main], cwd=source).returncode:
            raise ValueError(f"STOP_FROZEN_MAIN_NOT_ANCESTOR:{latest_main}")
        main_changes = subprocess.check_output(["git", "diff", "--name-only", frozen_main, latest_main], cwd=source, text=True).splitlines()
        protected = freeze["protected_main_paths"]
        collisions = [p for p in main_changes if any(p == prefix or p.startswith(prefix.rstrip("/") + "/") for prefix in protected)]
        if collisions:
            raise ValueError(f"STOP_MAIN_PROTECTED_PATH_ADVANCE:{collisions}")
        paths = subprocess.check_output(["git", "diff", "--name-only", frozen_main, freeze["source_commit"]], cwd=source, text=True).splitlines()
        allowed = freeze["additive_paths"]
        if any(not any(p == prefix or p.startswith(prefix.rstrip("/") + "/") for prefix in allowed) for p in paths):
            raise ValueError(f"STOP_NON_ADDITIVE_SOURCE:{paths}")
        stage = "runtime_identity"
        context = subprocess.check_output(["docker", "context", "show"], text=True).strip()
        if context != runtime["docker_context"]:
            raise ValueError(f"STOP_DOCKER_CONTEXT:{context}")
        identity = subprocess.check_output(["docker", "image", "inspect", runtime["image_id"], "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"], text=True).strip()
        if identity != f"{runtime['image_id']} {runtime['platform']}":
            raise ValueError(f"STOP_IMAGE_IDENTITY:{identity}")
        if subprocess.run(["docker", "container", "inspect", runtime["construction_container_name"]], text=True, capture_output=True).returncode == 0:
            raise ValueError("STOP_CONTAINER_NAME_COLLISION")
    except Exception as exc:
        stop = {"schema": "spatial-block-6590-training-parity-stop-v1", "allocation": freeze.get("allocation") if freeze else None,
                "stage": stage, "reason": f"{type(exc).__name__}: {exc}", "container_creations": 0,
                "candidate_fit_calls": 0, "auditor_fit_calls": 0, "retries": 0, "recorded_utc": now()}
        (output / "STOP.json").write_text(json.dumps(stop, indent=2, sort_keys=True) + "\n")
        print(json.dumps(stop, indent=2, sort_keys=True))
        return 1

    command = ["docker", "create", "--name", runtime["construction_container_name"], "--network=none", "--cpus=1", "--memory=2g",
               "--pids-limit=64", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--read-only",
               "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "-e", "OPENBLAS_NUM_THREADS=1",
               "--mount", f"type=bind,src={source},dst=/experiment,readonly",
               "--workdir=/experiment", "--entrypoint=python", runtime["image_id"], "-B", "-m", "unittest",
               "discover", "-s", ".", "-p", "test_*.py", "-v"]
    container_id = subprocess.check_output(command, text=True).strip()
    t0 = time.perf_counter()
    process = subprocess.run(["docker", "start", "--attach", container_id], text=True, capture_output=True, timeout=600)
    duration = time.perf_counter() - t0
    (output / "stdout.txt").write_text(process.stdout, encoding="utf-8")
    (output / "stderr.txt").write_text(process.stderr, encoding="utf-8")
    inspected = subprocess.check_output(["docker", "inspect", container_id], text=True)
    (output / "container-inspect.json").write_text(inspected, encoding="utf-8")
    state = json.loads(inspected)[0]["State"]
    subprocess.run(["docker", "rm", container_id], text=True, capture_output=True, timeout=30)
    passed = process.returncode == 0 and "Ran 9 tests" in process.stderr and "OK" in process.stderr
    record = {"schema": "spatial-block-6590-training-parity-run-v1", "allocation": freeze["construction_allocation"],
              "freeze_sha256": freeze_sha, "source_commit": head, "live_main_sha": latest_main,
              "main_advanced_disjointly": latest_main != freeze["main_sha"], "main_paths_advanced": main_changes,
              "image_id": runtime["image_id"], "docker_context": context, "command_argv": command,
              "container_id": container_id, "container_name": runtime["construction_container_name"],
              "container_state": state, "duration_seconds": duration, "exit_code": process.returncode,
              "candidate_fit_calls": 1, "auditor_fit_calls": 1, "retries": 0,
              "stdout_sha256": sha(output / "stdout.txt"), "stderr_sha256": sha(output / "stderr.txt"),
              "decision": "PASS_TRAINING_IMPLEMENTATION_REPRODUCIBLE" if passed else "HOLD_TRAINING_IMPLEMENTATION",
              "scope": "one synthetic training dataset; W1 update and exact candidate/auditor refit parity only; no spatial efficacy claim"}
    (output / "RUN_RECORD.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.source, args.output))
