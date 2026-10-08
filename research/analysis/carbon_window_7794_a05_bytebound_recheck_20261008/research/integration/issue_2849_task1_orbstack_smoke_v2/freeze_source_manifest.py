"""Freeze the source/runtime image closure before the one formal task call."""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[3]
EXPERIMENT = Path(__file__).resolve().parent
RUN = REPO / "research/integration/issue_2849_task1_orbstack_smoke_v2/evidence/formal-task1-seed-284902"
LIVE = REPO / "research/live_control"
IMPORT_ROOTS = [EXPERIMENT, REPO, LIVE, REPO / "research/observation_tiles",
                REPO / "research/observation_gating", REPO / "research/real_apps_v1",
                REPO / "runtime"]
ROOTS = [
    LIVE / "run_integrated_efficiency_live_v1.py",
    LIVE / "integrated_efficiency_client_v1.py",
    LIVE / "integrated_efficiency_model_v1.py",
    LIVE / "integrated_efficiency_protocol_v1.py",
    LIVE / "integrated_efficiency_fixture_v1.py",
    LIVE / "integrated_efficiency_runtime_v1.py",
    LIVE / "integrated_efficiency_socket_v1.py",
    LIVE / "interactive_integrated_efficiency_v1.py",
    LIVE / "interactive_v27.py",
    LIVE / "cause_servo_interactive_v4.py",
    LIVE / "cause_servo_session_v1.py",
    LIVE / "cause_session_v1.py",
    LIVE / "session_v33.py",
    LIVE / "executor_v4.py",
    LIVE / "event_socket_v11.py",
    LIVE / "plain_form_points_v1.py",
    LIVE / "plain_form_points_schema_v1.json",
    LIVE / "plain_form_points_responder_v1.txt",
    LIVE / "issue_2849_runner_aux_event_v2_v1/event_accounting.py",
    REPO / "runtime/docker_schema_preflight_v1.py",
    REPO / "runtime/host_model_ipc_broker_v1.py",
    EXPERIMENT / "Dockerfile",
    EXPERIMENT / "python-schema-requirements.lock",
    EXPERIMENT / "startup_check.py",
    EXPERIMENT / "run_task1_smoke.py",
    EXPERIMENT / "integrated_efficiency_socket_v1.py",
    EXPERIMENT / "interactive_integrated_efficiency_task1_v2.py",
    EXPERIMENT / "integrated_efficiency_runtime_task1_v2.py",
    EXPERIMENT / "freeze_source_manifest.py",
    EXPERIMENT / "audit_task1_smoke.py",
]
STDLIB = set("""__future__ os sys time json hashlib copy threading argparse contextlib
shutil subprocess tempfile re math random collections dataclasses enum typing pathlib
urllib http html socket select struct zlib io base64 binascii queue traceback weakref
signal platform fcntl logging abc inspect itertools statistics functools operator string
textwrap csv glob importlib uuid unittest multiprocessing concurrent asyncio ctypes
datetime colorsys warnings gc secrets xml codecs locale errno mmap resource stat
ast socketserver
""".split())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module_path(name: str) -> Path | None:
    relative = Path(*name.split("."))
    for root in IMPORT_ROOTS:
        candidate = root / relative.with_suffix(".py")
        if candidate.is_file():
            return candidate.resolve()
        package = root / relative / "__init__.py"
        if package.is_file():
            return package.resolve()
    top = name.split(".")[0]
    if top != name:
        return module_path(top)
    return None


def main() -> int:
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO,
                                   text=True).strip()
    latest_main = subprocess.check_output(
        ["git", "rev-parse", "refs/remotes/origin/main"], cwd=REPO,
        text=True).strip()
    pending = [path.resolve() for path in ROOTS]
    files: set[Path] = set()
    missing = []
    external = set()
    while pending:
        path = pending.pop()
        if path in files:
            continue
        if not path.is_file():
            missing.append(str(path.relative_to(REPO)))
            continue
        files.add(path)
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules = ([alias.name for alias in node.names]
                       if isinstance(node, ast.Import) else
                       [node.module]
                       if isinstance(node, ast.ImportFrom) and node.module else [])
            for name in modules:
                if name.split(".")[0] in STDLIB:
                    continue
                candidate = module_path(name)
                if candidate is None:
                    external.add(name.split(".")[0])
                elif candidate not in files:
                    pending.append(candidate)
    if missing:
        raise RuntimeError("STOP_SOURCE_CLOSURE_MISSING:" + ",".join(missing))
    upstream_entries = [path for path in files
                        if not path.is_relative_to(EXPERIMENT)]
    changed_on_latest_main = []
    for path in upstream_entries:
        relative = str(path.relative_to(REPO))
        current = subprocess.run(["git", "show", "origin/main:" + relative],
                                 cwd=REPO, capture_output=True, check=False)
        if current.returncode or hashlib.sha256(current.stdout).hexdigest() != sha(path):
            changed_on_latest_main.append(relative)
    if changed_on_latest_main:
        raise RuntimeError("STOP_SOURCE_CLOSURE_CHANGED_ON_LATEST_MAIN:" +
                           ",".join(changed_on_latest_main))
    entries = [{"path": str(path.relative_to(REPO)), "sha256": sha(path)}
               for path in sorted(files)]
    startup_path = REPO / "research/integration/issue_2849_task1_orbstack_smoke_v2/evidence/startup-gate/run-10/startup-result.json"
    startup = json.loads(startup_path.read_text(encoding="utf-8"))
    if startup.get("status") != "PASS_RUNTIME_STARTUP_NO_MODEL" or startup.get("model_calls") != 0:
        raise RuntimeError("STOP_STARTUP_GATE_NOT_PASS")
    docker_output = subprocess.check_output([
        "docker", "--context", "orbstack", "run", "--rm", "--network", "none",
        "--entrypoint", "/bin/sh", "issue-2849-task1-runtime:20260921", "-lc",
        "dpkg-query -W -f='${Package}=${Version}\\n' | sort; python3 -m pip freeze --all | sort; chromium --version; docker --version",
    ], text=True)
    images = {}
    for tag in ("issue-2849-task1-runtime:20260921",
                "python:3.12-slim"):
        image_id = subprocess.check_output([
            "docker", "--context", "orbstack", "image", "inspect", tag,
            "--format", "{{.Id}} {{.Architecture}}",
        ], text=True).strip()
        images[tag] = image_id
    os.environ["CODEX_EXE"] = "/opt/homebrew/bin/codex"
    sys.path.insert(0, str(REPO / "runtime"))
    from host_model_ipc_broker_v1 import executable_identity
    host_model = executable_identity(os.environ["CODEX_EXE"])
    manifest = {
        "status": "FROZEN_BEFORE_MODEL_CALL",
        "repository": "Unjuno/agent-interface",
        "source_base_commit": base,
        "latest_main_commit_at_freeze": latest_main,
        "source_paths_verified_byte_identical_on_latest_main": len(upstream_entries),
        "source_files": entries,
        "source_file_count": len(entries),
        "external_python_imports": sorted(external),
        "container_images": images,
        "container_packages_and_tool_versions": docker_output.splitlines(),
        "host_model_cli": host_model,
        "startup_gate": startup,
        "task_seed": 284902,
        "task_scope": "task-1/layout-A/cold/plain",
        "model_call_limit": 1,
        "network_policy": "outer-runtime-and-inner-model-containers --network none",
        "authority_granted": False,
    }
    RUN.mkdir(parents=True, exist_ok=True)
    (RUN / "pre-call-source-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({"status": manifest["status"], "source_base_commit": base,
                      "source_file_count": len(entries),
                      "external_python_imports": sorted(external),
                      "container_images": images,
                      "manifest": str(RUN / "pre-call-source-manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
