"""One-shot host runner for the frozen #6590 OrbStack allocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args) -> int:
    source = args.source.resolve()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_ABSENT")
    output.mkdir(parents=True, exist_ok=True)
    stage = "freeze_readback"
    try:
        freeze_file = source / "FREEZE.json"
        sidecar = source / "FREEZE.sha256"
        freeze_bytes = freeze_file.read_bytes()
        expected_freeze_sha = sidecar.read_text(encoding="ascii").split()[0]
        if digest(freeze_file) != expected_freeze_sha:
            raise ValueError("STOP_FREEZE_SIDECAR_MISMATCH")
        freeze = json.loads(freeze_bytes)
        stage = "frozen_source_hashes"
        for relative, expected in freeze["source_sha256"].items():
            actual = digest(source / relative)
            if actual != expected:
                raise ValueError(f"STOP_SOURCE_HASH_MISMATCH:{relative}:{actual}")
        stage = "git_head_and_main"
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
        parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=source, text=True).strip()
        frozen_main = freeze["main_sha"]
        ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", frozen_main, parent],
                                  cwd=source, text=True, capture_output=True)
        if ancestry.returncode != 0:
            raise ValueError(f"STOP_SOURCE_BASE_NOT_FROZEN_MAIN:{parent}")
        if parent != freeze["source_commit"]:
            raise ValueError(f"STOP_SOURCE_COMMIT_MISMATCH:{head}:parent={parent}")
        changed = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                                          cwd=source, text=True).splitlines()
        repo_root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                                  cwd=source, text=True).strip())
        expected_freeze_paths = sorted([str(freeze_file.relative_to(repo_root)),
                                        str(sidecar.relative_to(repo_root))])
        if sorted(changed) != expected_freeze_paths:
            raise ValueError(f"STOP_FREEZE_COMMIT_SCOPE_MISMATCH:{changed}")
        worktree = subprocess.check_output(["git", "status", "--porcelain"], cwd=source, text=True)
        if worktree.strip():
            raise ValueError("STOP_DIRTY_WORKTREE")
        main_row = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"],
                                           cwd=source, text=True).strip().split()
        live_main = main_row[0] if main_row else ""
        ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", live_main, head],
                                  cwd=source, text=True, capture_output=True)
        if ancestor.returncode != 0:
            raise ValueError(f"STOP_LIVE_MAIN_NOT_ANCESTOR_OF_SOURCE:{live_main}")
        main_changes = subprocess.check_output(["git", "diff", "--name-only",
                                                live_main, head],
                                               cwd=source, text=True).splitlines()
        package_prefix = freeze["package_path"].rstrip("/") + "/"
        collisions = [path for path in main_changes if not path.startswith(package_prefix)
                      and path != ".github/workflows/spatial-block-6590-t1.yml"]
        if collisions:
            raise ValueError(f"STOP_SOURCE_NOT_ADDITIVE:{collisions}")
        stage = "docker_runtime_identity"
        context = subprocess.check_output(["docker", "context", "show"], text=True).strip()
        if context != freeze["runtime"]["docker_context"]:
            raise ValueError(f"STOP_CONTEXT_MISMATCH:{context}")
        image = subprocess.check_output(["docker", "image", "inspect", freeze["runtime"]["image_id"],
                                         "--format", "{{.Id}} {{.Os}}/{{.Architecture}}"],
                                        text=True).strip()
        if image != f"{freeze['runtime']['image_id']} {freeze['runtime']['platform']}":
            raise ValueError(f"STOP_IMAGE_IDENTITY_MISMATCH:{image}")
        for name in (freeze["runtime"]["candidate_container_name"],
                     freeze["runtime"]["auditor_container_name"]):
            probe = subprocess.run(["docker", "container", "inspect", name],
                                   text=True, capture_output=True)
            if probe.returncode == 0:
                raise ValueError(f"STOP_CONTAINER_NAME_COLLISION:{name}")
    except Exception as exc:
        stop = {"schema": "spatial-block-position-6590-t1-prelaunch-stop-v1",
                "allocation": freeze.get("allocation") if "freeze" in locals() else None,
                "stage": stage, "reason": f"{type(exc).__name__}: {exc}",
                "candidate_invocations": 0, "auditor_invocations": 0,
                "container_creations": 0, "retries": 0, "recorded_utc": utc_now()}
        (output / "PRELAUNCH_STOP.json").write_text(json.dumps(stop, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(stop, indent=2, sort_keys=True))
        return 1
    runtime = output / "runtime"
    runtime.mkdir()

    source_mount = str(source)
    candidate_dir = output / "candidate"
    audit_dir = output / "audit"
    candidate_dir.mkdir()
    audit_dir.mkdir()
    record = {"schema": "spatial-block-position-6590-t1-orbstack-run-v1",
              "allocation": freeze["allocation"], "freeze_sha256": expected_freeze_sha,
              "source_commit": head, "main_sha_at_freeze": freeze["main_sha"],
              "live_main_sha_prelaunch": live_main,
              "main_advanced_disjointly": live_main != freeze["main_sha"],
              "main_paths_advanced_disjointly": main_changes,
              "docker_context": context,
              "image_inspect": image, "candidate_invocations": 0,
              "auditor_invocations": 0, "retries": 0, "candidate": None,
              "auditor": None, "decision": "STOP_BEFORE_CANDIDATE"}

    def invoke(role: str, name: str, mounts: list[tuple[str, str, bool]], argv: list[str]) -> dict:
        create = ["docker", "create", "--name", name, "--network=none", "--cpus=1",
                  "--memory=2g", "--pids-limit=64", "--cap-drop=ALL",
                  "--security-opt=no-new-privileges", "--read-only",
                  "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                  "-e", "OPENBLAS_NUM_THREADS=1"]
        for host_path, target, readonly in mounts:
            mode = ",readonly" if readonly else ""
            create.extend(["--mount", f"type=bind,src={host_path},dst={target}{mode}"])
        create.extend(["--workdir=/experiment", "--entrypoint=python", freeze["runtime"]["image_id"]])
        create.extend(argv)
        command_argv = list(create)
        container_id = subprocess.check_output(command_argv, text=True).strip()
        started_at = utc_now()
        t0 = time.perf_counter()
        try:
            process = subprocess.run(["docker", "start", "--attach", container_id],
                                     text=True, capture_output=True, timeout=1800)
            exit_code = process.returncode
            stdout, stderr = process.stdout, process.stderr
        except subprocess.TimeoutExpired as exc:
            subprocess.run(["docker", "stop", "--time=0", container_id],
                           text=True, capture_output=True, timeout=20)
            exit_code = 124
            stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        duration = time.perf_counter() - t0
        stdout_path = runtime / f"{role}.stdout.txt"
        stderr_path = runtime / f"{role}.stderr.txt"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        inspected = subprocess.check_output(["docker", "inspect", container_id], text=True)
        inspect_path = runtime / f"{role}.container-inspect.json"
        inspect_path.write_text(inspected, encoding="utf-8")
        state = json.loads(inspected)[0]["State"]
        ended_at = utc_now()
        subprocess.run(["docker", "rm", container_id], text=True, capture_output=True, timeout=30)
        return {"container_id": container_id, "container_name": name,
                "started_utc": started_at, "ended_utc": ended_at,
                "duration_seconds": duration, "exit_code": exit_code,
                "docker_state": state, "command_argv": command_argv,
                "stdout": stdout_path.name, "stderr": stderr_path.name,
                "inspect": inspect_path.name,
                "stdout_sha256": digest(stdout_path), "stderr_sha256": digest(stderr_path)}

    candidate = invoke("candidate", freeze["runtime"]["candidate_container_name"],
                       [(source_mount, "/experiment", True),
                        (str(candidate_dir), "/out", False)],
                       ["-B", "/experiment/candidate.py", "--root", "/experiment", "--out", "/out"])
    record["candidate"] = candidate
    record["candidate_invocations"] = 1
    if candidate["exit_code"] != 0:
        record["decision"] = "STOP_CANDIDATE_NONZERO"
    else:
        auditor = invoke("auditor", freeze["runtime"]["auditor_container_name"],
                         [(source_mount, "/experiment", True),
                          (str(candidate_dir), "/candidate", True),
                          (str(audit_dir), "/audit", False)],
                         ["-B", "/experiment/auditor.py", "--root", "/experiment", "--out", "/audit"])
        record["auditor"] = auditor
        record["auditor_invocations"] = 1
        if auditor["exit_code"] != 0:
            record["decision"] = "STOP_AUDITOR_NONZERO"
        else:
            audit_path = audit_dir / "AUDIT.json"
            audit_result = json.loads(audit_path.read_text(encoding="utf-8"))
            record["decision"] = audit_result["decision"]
            record["audit_sha256"] = digest(audit_path)
    record["runtime_probes"] = {"orbctl_status": subprocess.run(["orbctl", "status"],
                                                                    text=True, capture_output=True).stdout.strip(),
                                 "container_inventory_not_read": True}
    (output / "RUN_RECORD.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["decision"] in ("H_PASS_SCOPED", "H_FAIL_SCOPED", "HOLD_MODEL_INCOMPETENT_OR_FALSE_ACCEPT", "HOLD_AUDIT_INTEGRITY") else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    raise SystemExit(run(parser.parse_args()))
