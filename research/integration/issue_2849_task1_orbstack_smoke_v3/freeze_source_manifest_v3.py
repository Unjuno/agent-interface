"""Freeze v3 sources, image/package identities, and no-model gate before task."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[3]
V2 = REPO / "research/integration/issue_2849_task1_orbstack_smoke_v2"
HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence/formal-task1-seed-284903"
V3_FILES = [HERE / name for name in (
    "Dockerfile", "python-requirements.lock", "startup_gate_v3.py",
    "run_attempt_v3.py", "freeze_source_manifest_v3.py", "audit_task1_v3.py")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    prior_path = V2 / "evidence/formal-task1-seed-284902/pre-call-source-manifest.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    for item in prior["source_files"]:
        path = REPO / item["path"]
        if not path.is_file() or sha(path) != item["sha256"]:
            raise RuntimeError("STOP_PREDECESSOR_SOURCE_CHANGED:" + item["path"])
    current_main = subprocess.check_output(
        ["git", "rev-parse", "refs/remotes/origin/main"], cwd=REPO,
        text=True).strip()
    upstream_count = 0
    for item in prior["source_files"]:
        if item["path"].startswith(
                "research/integration/issue_2849_task1_orbstack_smoke_v2/"):
            continue
        data = subprocess.check_output(["git", "show", "origin/main:" + item["path"]],
                                       cwd=REPO, stderr=subprocess.DEVNULL)
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise RuntimeError("STOP_SOURCE_CHANGED_ON_LATEST_MAIN:" + item["path"])
        upstream_count += 1
    entries = list(prior["source_files"])
    entries += [{"path": str(path.relative_to(REPO)), "sha256": sha(path)}
                for path in V3_FILES]
    startup_path = HERE / "evidence/startup-gate/run-1/startup-result.json"
    startup = json.loads(startup_path.read_text(encoding="utf-8"))
    if startup.get("status") != "PASS_RUNTIME_STARTUP_NO_MODEL":
        raise RuntimeError("STOP_V3_STARTUP_GATE_NOT_PASS")
    package_output = subprocess.check_output([
        "docker", "--context", "orbstack", "run", "--rm", "--network", "none",
        "--entrypoint", "/bin/sh", "issue-2849-task1-runtime:v3-20260921", "-lc",
        "python3 --version; python3 -m pip freeze --all | sort; "
        "python3 -c 'import referencing, typing_extensions; "
        "from typing import Any; T=typing_extensions.TypeVar(\"T\", default=Any); "
        "from referencing import Registry; print(\"referencing-TypeVar-default-ok\", T, Registry)'",
    ], text=True)
    image_id = subprocess.check_output([
        "docker", "--context", "orbstack", "image", "inspect",
        "issue-2849-task1-runtime:v3-20260921", "--format", "{{.Id}} {{.Architecture}}",
    ], text=True).strip()
    RUN.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "FROZEN_BEFORE_MODEL_CALL",
        "source_base_commit": prior["source_base_commit"],
        "latest_main_commit_at_freeze": current_main,
        "byte_identical_main_source_paths_verified": upstream_count,
        "source_files": entries,
        "source_file_count": len(entries),
        "container_images": {
            "outer": image_id,
            "nested_model": prior["container_images"]["python:3.12-slim"],
        },
        "outer_python_packages": package_output.splitlines(),
        "predecessor_stop": json.loads((V2 /
            "evidence/formal-task1-seed-284902/attempt-stop.json").read_text()),
        "startup_gate": startup,
        "task_seed": 284903,
        "task_scope": "task-1/layout-A/cold/plain",
        "model_call_limit": 1,
        "authority_granted": False,
        "network_policy": "outer-runtime-and-inner-model-containers --network none",
    }
    (RUN / "pre-call-source-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({"status": manifest["status"], "source_file_count": len(entries),
                      "latest_main": current_main, "main_paths_verified": upstream_count,
                      "outer_image": image_id,
                      "manifest": str(RUN / "pre-call-source-manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
