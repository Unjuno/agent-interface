"""Docker-backed model-call contract for the integrated-efficiency seam.

This module deliberately requires explicit paths and image configuration. It
does not fall back to the legacy WSL caller and reports malformed/missing
container receipts as failures.
"""
from __future__ import annotations

from contextlib import contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

CLIENT_TIMEOUT_SECONDS = 90


def _contract_setting(name: str, contract: str) -> str:
    return (os.environ.get(f"AGENT_INTERFACE_DOCKER_{name}_{contract.upper()}")
            or os.environ.get(f"AGENT_INTERFACE_DOCKER_{name}", ""))


def runtime_identity() -> tuple[str, str]:
    image = os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE", "")
    platform = os.environ.get("AGENT_INTERFACE_DOCKER_PLATFORM", "")
    if not re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", image):
        raise RuntimeError("STOP_DOCKER_BACKEND_IMAGE_NOT_DIGEST_PINNED")
    if platform not in {"linux/arm64", "linux/amd64"}:
        raise RuntimeError("STOP_DOCKER_BACKEND_PLATFORM_NOT_PINNED")
    return image, platform


@contextmanager
def _host_repo_mapping_lock():
    """Serialize staging and use of the broker's shared /repo mapping."""
    raw_repo = os.environ.get("AGENT_INTERFACE_DOCKER_HOST_REPO", "")
    if not raw_repo:
        raise RuntimeError("STOP_DOCKER_BACKEND_HOST_REPO_UNCONFIGURED")
    host_repo = Path(raw_repo).resolve()
    if not host_repo.is_dir():
        raise FileNotFoundError(host_repo)
    with (host_repo / ".host-model-ipc-path-map.lock").open("a+b") as lock_file:
        if os.name == "nt":
            import msvcrt
            lock_file.seek(0)
            if lock_file.read(1) == b"":
                lock_file.seek(0)
                lock_file.write(b"0")
                lock_file.flush()
            lock_file.seek(0)
            while True:
                try:
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    if (error.errno not in (errno.EACCES, errno.EDEADLK)
                            and getattr(error, "winerror", None) not in (33, 36)):
                        raise
                    time.sleep(0.05)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _diagnostic_tail(value):
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='replace')
    return (value or '')[-2000:]


def _stage_host_repo(root: Path, runner: Path, schema: Path,
                     instructions: Path, prompt: Path,
                     workspace: Path, image: Path | None = None) -> None:
    """Make the host broker's fixed /repo paths resolve to this call's inputs."""
    raw_repo = os.environ.get("AGENT_INTERFACE_DOCKER_HOST_REPO", "")
    if not raw_repo:
        raise RuntimeError("STOP_DOCKER_BACKEND_HOST_REPO_UNCONFIGURED")
    host_repo = Path(raw_repo).resolve()
    if not host_repo.is_dir():
        raise FileNotFoundError(host_repo)
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    sources = {"runner.py": Path(runner), "schema.json": Path(schema),
               "instructions.txt": Path(instructions), "prompt.txt": Path(prompt),
               "workspace": Path(workspace)}
    if image is not None:
        sources["image.png"] = Path(image)
    mapping = {}
    for name, source in sources.items():
        target = source.resolve(strict=True)
        if name == "workspace":
            if not target.is_dir():
                raise NotADirectoryError(target)
        elif not target.is_file():
            raise FileNotFoundError(target)
        link = host_repo / name
        if link.exists() and not link.is_symlink():
            raise FileExistsError("host IPC mapping target is not a symlink: " + str(link))
        temporary = host_repo / ("." + name + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporary.symlink_to(target, target_is_directory=(name == "workspace"))
            os.replace(temporary, link)
        finally:
            temporary.unlink(missing_ok=True)
        key = name.removesuffix(".py").removesuffix(".json").removesuffix(".txt").removesuffix(".png")
        mapping[key] = {"host_path": str(target),
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest()
                        if target.is_file() else None}
    (root / "host-path-map.json").write_text(
        json.dumps({"schema": "docker-host-ipc-path-map-v1",
                    "host_repo": str(host_repo), "paths": mapping}, indent=2) + "\n",
        encoding="utf-8")


def _verify_host_repo_mapping(root: Path, schema: Path,
                              instructions: Path, workspace: Path,
                              image: Path | None) -> None:
    repo = Path(os.environ["AGENT_INTERFACE_DOCKER_HOST_REPO"]).resolve()
    data = json.loads((Path(root) / "host-path-map.json").read_text(encoding="utf-8"))
    expected = {"schema": (Path(schema), "schema.json"),
                "instructions": (Path(instructions), "instructions.txt"),
                "workspace": (Path(workspace), "workspace"),
                "runner": (Path(os.environ["AGENT_INTERFACE_DOCKER_RUNNER"]), "runner.py"),
                "prompt": (Path(root) / "prompt.txt", "prompt.txt")}
    if image is not None:
        expected["image"] = (Path(image), "image.png")
    if data.get("schema") != "docker-host-ipc-path-map-v1" or data.get("host_repo") != str(repo):
        raise ValueError("host IPC path-map identity mismatch")
    for name, (source, filename) in expected.items():
        target = source.resolve(strict=True)
        link = repo / filename
        record = data.get("paths", {}).get(name)
        expected_hash = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        if (not isinstance(record, dict) or record.get("host_path") != str(target)
                or record.get("sha256") != expected_hash
                or not link.is_symlink() or link.resolve(strict=True) != target):
            raise ValueError("host IPC path-map target mismatch: " + name)


def _capture_host_ipc(root: Path, ipc: Path, process: dict,
                      schema: Path, instructions: Path,
                      events_path: Path, *, mode: str = "handle",
                      image_sha256: str | None = None,
                      workspace: Path, image: Path | None = None) -> dict:
    request_id = process.get("request_id")
    if (not isinstance(request_id, str) or len(request_id) != 32
            or any(character not in "0123456789abcdef" for character in request_id)):
        raise ValueError("host IPC request id is missing or malformed")
    names = {"request": f"{request_id}.request.json",
             "broker": f"{request_id}.broker.json",
             "response": f"{request_id}.response.jsonl"}
    paths = {name: Path(ipc) / filename for name, filename in names.items()}
    deadline = time.monotonic() + 2.0
    while not all(path.is_file() for path in paths.values()) and time.monotonic() < deadline:
        time.sleep(0.02)
    if not all(path.is_file() for path in paths.values()):
        raise FileNotFoundError("host IPC request/broker/response receipt missing")
    request = json.loads(paths["request"].read_text(encoding="utf-8"))
    broker = json.loads(paths["broker"].read_text(encoding="utf-8"))
    response = paths["response"].read_bytes()
    if (request.get("request_id") != request_id or request.get("mode") != mode
            or request.get("image_sha256") != image_sha256
            or ((mode == "handle") != (request.get("image") is None))
            or request.get("authority_granted") is not False
            or request.get("schema_sha256") != hashlib.sha256(Path(schema).read_bytes()).hexdigest()
            or request.get("instructions_sha256") != hashlib.sha256(
                Path(instructions).read_bytes()).hexdigest()):
        raise ValueError("host IPC request identity does not match the preflight")
    expected_image = None if mode == "handle" else "/repo/image.png"
    if (request.get("schema") != "/repo/schema.json"
            or request.get("working") != "/repo/workspace"
            or request.get("image") != expected_image):
        raise ValueError("host IPC paths do not match the fixed broker mapping")
    _verify_host_repo_mapping(root, schema, instructions, workspace, image)
    expected_host_paths = {
        "schema": str(Path(schema).resolve()),
        "working": str(Path(workspace).resolve()),
        "image": None if image is None else str(Path(image).resolve()),
    }
    if (broker.get("request_id") != request_id or broker.get("returncode") != 0
            or broker.get("boundary") != "host-local-codex-exe"
            or broker.get("authority_granted") is not False
            or broker.get("resolved_paths") != expected_host_paths):
        raise ValueError("host broker receipt does not confirm one successful call")
    if response != Path(events_path).read_bytes():
        raise ValueError("host IPC response differs from runner event stream")
    retained = Path(root) / "host-ipc"
    retained.mkdir(exist_ok=False)
    for name, path in paths.items():
        suffix = {"request": "request.json", "broker": "broker.json",
                  "response": "response.jsonl"}[name]
        (retained / suffix).write_bytes(path.read_bytes())
    summary = {"request_id": request_id, "request_sha256": hashlib.sha256(
                paths["request"].read_bytes()).hexdigest(),
            "broker_sha256": hashlib.sha256(paths["broker"].read_bytes()).hexdigest(),
            "response_sha256": hashlib.sha256(response).hexdigest(),
            "boundary": broker["boundary"], "host_cli_returncode": broker["returncode"]}
    (retained / "receipt.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def build_command(root: Path, prompt: str, image: Path, contract: str, workspace: Path) -> list[str]:
    runner = os.environ.get("AGENT_INTERFACE_DOCKER_RUNNER", "")
    image_name = os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE", "")
    ipc = os.environ.get("AGENT_INTERFACE_DOCKER_IPC", "")
    host_repo = os.environ.get("AGENT_INTERFACE_DOCKER_HOST_REPO", "")
    raw_platform = os.environ.get("AGENT_INTERFACE_DOCKER_PLATFORM", "")
    if contract not in ("plain", "compiled"):
        raise ValueError("contract must be plain or compiled")
    schema = _contract_setting("SCHEMA", contract)
    instructions = _contract_setting("INSTRUCTIONS", contract)
    if not all((runner, schema, instructions, image_name, ipc, host_repo, raw_platform)):
        raise RuntimeError("STOP_DOCKER_BACKEND_UNCONFIGURED")
    image_name, platform = runtime_identity()
    for value in (runner, schema, instructions, prompt, image, workspace, Path(ipc)):
        if not Path(value).exists():
            raise FileNotFoundError(value)
    _stage_host_repo(root, Path(runner), Path(schema), Path(instructions),
                     Path(prompt), Path(workspace), Path(image))
    command = [
        os.environ.get("DOCKER", "docker"), "run", "--pull=never",
        "--platform", platform, "--rm", "--network", "none",
        "-e", "HOST_MODEL_IPC_DIR=/ipc",
        "-v", f"{Path(root).resolve()}:/out",
        "-v", f"{Path(ipc).resolve()}:/ipc",
        "-v", f"{Path(runner).resolve()}:/repo/runner.py:ro",
        "-v", f"{Path(schema).resolve()}:/repo/schema.json:ro",
        "-v", f"{Path(instructions).resolve()}:/repo/instructions.txt:ro",
        "-v", f"{Path(prompt).resolve()}:/repo/prompt.txt:ro",
        "-v", f"{Path(image).resolve()}:/repo/image.png:ro",
        "-v", f"{Path(workspace).resolve()}:/repo/workspace",
        image_name, "python", "/repo/runner.py",
        "/usr/bin/node", "/usr/bin/true", "/repo/prompt.txt",
        "/repo/workspace", "/out/runner", "coordinate", "/repo/image.png",
        "/repo/instructions.txt", "/repo/schema.json",
    ]
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        command[7:7] = [
            "-e", f"HOST_MODEL_IPC_OWNER_UID={os.getuid()}",
            "-e", f"HOST_MODEL_IPC_OWNER_GID={os.getgid()}",
        ]
    return command


def build_preflight_command(root: Path, schema: Path, instructions: Path,
                            workspace: Path) -> list[str]:
    """Build a no-image host-IPC request for endpoint/schema compatibility."""
    runner = os.environ.get("AGENT_INTERFACE_DOCKER_RUNNER", "")
    image_name = os.environ.get("AGENT_INTERFACE_DOCKER_IMAGE", "")
    ipc = os.environ.get("AGENT_INTERFACE_DOCKER_IPC", "")
    host_repo = os.environ.get("AGENT_INTERFACE_DOCKER_HOST_REPO", "")
    raw_platform = os.environ.get("AGENT_INTERFACE_DOCKER_PLATFORM", "")
    root = Path(root).resolve()
    if not all((runner, image_name, ipc, host_repo, raw_platform)):
        raise RuntimeError("STOP_DOCKER_BACKEND_UNCONFIGURED")
    image_name, platform = runtime_identity()
    for value in (runner, schema, instructions, workspace, Path(ipc)):
        if not Path(value).exists():
            raise FileNotFoundError(value)
    if not root.is_dir():
        raise FileNotFoundError(root)
    _stage_host_repo(root, Path(runner), Path(schema), Path(instructions),
                     root / "prompt.txt", Path(workspace))
    command = [
        os.environ.get("DOCKER", "docker"), "run", "--pull=never",
        "--platform", platform, "--rm", "--network", "none",
        "-e", "HOST_MODEL_IPC_DIR=/ipc",
        "-v", f"{root}:/out",
        "-v", f"{Path(ipc).resolve()}:/ipc",
        "-v", f"{Path(runner).resolve()}:/repo/runner.py:ro",
        "-v", f"{Path(schema).resolve()}:/repo/schema.json:ro",
        "-v", f"{Path(instructions).resolve()}:/repo/instructions.txt:ro",
        "-v", f"{root / 'prompt.txt'}:/repo/prompt.txt:ro",
        "-v", f"{Path(workspace).resolve()}:/repo/workspace",
        image_name, "python", "/repo/runner.py",
        "/usr/bin/node", "/usr/bin/true", "/repo/prompt.txt",
        "/repo/workspace", "/out/runner", "handle", "-",
        "/repo/instructions.txt", "/repo/schema.json",
    ]
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        owner_env = ["-e", f"HOST_MODEL_IPC_OWNER_UID={os.getuid()}",
                     "-e", f"HOST_MODEL_IPC_OWNER_GID={os.getgid()}"]
        command[2:2] = owner_env
    return command


def _preflight_schema_locked(root: Path, schema: Path, instructions: Path,
                             workspace: Path) -> dict:
    """Issue one fresh, no-image schema endpoint request through host IPC.

    The result is intentionally separate from task scoring. A timeout or any
    malformed/missing receipt is terminal and is never retried.
    """
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    prompt = ("Schema compatibility probe. Produce a JSON object accepted by "
              "the supplied output schema. Do not call tools, edit files, or "
              "claim task completion.")
    (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    image_identity = runtime_identity()
    command = build_preflight_command(root, schema, instructions, workspace)
    (root / "preflight-attempt.json").write_text(json.dumps({
        "status": "starting", "started_ns": time.time_ns(),
        "timeout_seconds": CLIENT_TIMEOUT_SECONDS, "command": command,
        "container_image_ref": image_identity[0], "container_platform": image_identity[1],
        "image_count": 0, "retry_count": 0,
    }, indent=2) + "\n", encoding="utf-8")
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   check=False, timeout=CLIENT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        for name, value in (("stdout", error.stdout), ("stderr", error.stderr)):
            (root / ("runner-" + name + ".txt")).write_text(
                _diagnostic_tail(value), encoding="utf-8")
        (root / "preflight-result.json").write_text(json.dumps({
            "status": "STOP_DOCKER_PREFLIGHT_TIMEOUT", "ended_ns": time.time_ns(),
            "timeout_seconds": CLIENT_TIMEOUT_SECONDS, "returncode": None,
            "container_state": "unknown", "host_model_state": "unknown",
            "retry_performed": False, "model_visible_images": 0,
        }, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(
            "STOP_DOCKER_PREFLIGHT_TIMEOUT; remote execution state unknown; no retry"
        ) from error
    (root / "runner-stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (root / "runner-stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        result = {"status": "STOP_DOCKER_PREFLIGHT_RUNNER",
                  "returncode": completed.returncode, "retry_performed": False,
                  "container_state": "exited", "host_model_state": "unknown",
                  "model_visible_images": 0}
        (root / "preflight-result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("STOP_DOCKER_PREFLIGHT_RUNNER:" + str(completed.returncode))
    receipt = root / "runner" / "process.json"
    events_path = root / "runner" / "events.jsonl"
    if not receipt.is_file() or not events_path.is_file():
        result = {"status": "STOP_DOCKER_PREFLIGHT_MISSING_RECEIPT",
                  "retry_performed": False, "container_state": "exited",
                  "host_model_state": "unknown", "model_visible_images": 0}
        (root / "preflight-result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("STOP_DOCKER_PREFLIGHT_MISSING_RECEIPT")

    from runtime.docker_schema_preflight_v1 import validate_model_response
    validation = validate_model_response(events_path, Path(schema))
    try:
        rows = [json.loads(line) for line in events_path.read_text(
            encoding="utf-8").splitlines() if line.strip()]
        process = json.loads(receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        result = {"status": "STOP_DOCKER_PREFLIGHT_MALFORMED_RECEIPT",
                  "retry_performed": False, "container_state": "exited",
                  "host_model_state": "returned", "model_visible_images": 0}
        (root / "preflight-result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("STOP_DOCKER_PREFLIGHT_MALFORMED_RECEIPT")
    try:
        ipc_receipt = _capture_host_ipc(
            root, Path(os.environ["AGENT_INTERFACE_DOCKER_IPC"]), process,
            Path(schema), Path(instructions), events_path, mode="handle",
            workspace=Path(workspace))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, KeyError) as error:
        result = {"status": "STOP_DOCKER_PREFLIGHT_IPC_RECEIPT",
                  "error_class": type(error).__name__, "retry_performed": False,
                  "container_state": "exited", "host_model_state": "returned",
                  "model_visible_images": 0}
        (root / "preflight-result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("STOP_DOCKER_PREFLIGHT_IPC_RECEIPT") from error
    threads = [row["thread_id"] for row in rows
               if row.get("type") == "thread.started"
               and isinstance(row.get("thread_id"), str)]
    usage = validation.get("usage")
    usage_valid = (isinstance(usage, dict)
                   and all(type(usage.get(name)) is int and usage[name] >= 0
                           for name in ("input_tokens", "output_tokens")))
    if (validation.get("status") != "PASS" or len(threads) != 1
            or not usage_valid or process.get("mode") != "handle"
            or process.get("requested_model") != "gpt-5.6-luna"
            or process.get("requested_effort") != "low"):
        result = {"status": "STOP_DOCKER_PREFLIGHT_OUTPUT",
                  "validation": validation, "retry_performed": False,
                  "container_state": "exited", "host_model_state": "returned",
                  "model_visible_images": 0}
        (root / "preflight-result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("STOP_DOCKER_PREFLIGHT_OUTPUT:" +
                           str(validation.get("status")))
    result = {"status": "ENDPOINT_COMPATIBLE", "fresh": True,
              "call_id": threads[0], "usage": usage,
              "container_image_ref": image_identity[0],
              "container_platform": image_identity[1],
              "requested_model": process.get("requested_model"),
              "requested_effort": process.get("requested_effort"),
              "model_visible_images": 0, "retry_performed": False,
              "schema_validation": validation, "host_ipc": ipc_receipt}
    (root / "preflight-result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _call_locked(root: Path, prompt: str, image: Path, contract: str, workspace: Path):
    root.mkdir(parents=True, exist_ok=False)
    prompt_path = root / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    image_identity = runtime_identity()
    command = build_command(root, prompt_path, image, contract, workspace)
    schema_path = Path(_contract_setting("SCHEMA", contract))
    instructions_path = Path(_contract_setting("INSTRUCTIONS", contract))
    (root / 'client-attempt.json').write_text(json.dumps({
        'status': 'starting', 'started_ns': time.time_ns(),
        'timeout_seconds': CLIENT_TIMEOUT_SECONDS, 'command': command,
        'container_image_ref': image_identity[0], 'container_platform': image_identity[1],
    }, indent=2) + '\n', encoding='utf-8')
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False,
                                   timeout=CLIENT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        for name, value in (('stdout', error.stdout), ('stderr', error.stderr)):
            (root / ('runner-' + name + '.txt')).write_text(
                _diagnostic_tail(value), encoding='utf-8')
        (root / 'client-result.json').write_text(json.dumps({
            'status': 'STOP_DOCKER_BACKEND_TIMEOUT', 'ended_ns': time.time_ns(),
            'timeout_seconds': CLIENT_TIMEOUT_SECONDS, 'returncode': None,
            'container_state': 'unknown', 'host_model_state': 'unknown',
            'retry_performed': False, 'diagnostic_limit_characters': 2000,
        }, indent=2) + '\n', encoding='utf-8')
        raise RuntimeError('STOP_DOCKER_BACKEND_TIMEOUT; remote execution state unknown; no retry') from error
    (root / 'client-result.json').write_text(json.dumps({
        'status': 'returned', 'ended_ns': time.time_ns(), 'returncode': completed.returncode,
    }, indent=2) + '\n', encoding='utf-8')
    (root / 'runner-stdout.txt').write_text(completed.stdout, encoding='utf-8')
    (root / 'runner-stderr.txt').write_text(completed.stderr, encoding='utf-8')
    if completed.returncode != 0:
        raise RuntimeError("STOP_DOCKER_BACKEND_RUNNER:" + str(completed.returncode))
    receipt = root / "runner" / "process.json"
    events = root / "runner" / "events.jsonl"
    if not receipt.is_file() or not events.is_file():
        raise RuntimeError("STOP_DOCKER_BACKEND_MISSING_RECEIPT")
    ipc_receipt = None
    if os.environ.get("AGENT_INTERFACE_DOCKER_IPC"):
        try:
            process = json.loads(receipt.read_text(encoding="utf-8"))
            ipc_receipt = _capture_host_ipc(
                root, Path(os.environ["AGENT_INTERFACE_DOCKER_IPC"]), process,
                schema_path, instructions_path, events, mode="coordinate",
                image_sha256=hashlib.sha256(Path(image).read_bytes()).hexdigest(),
                workspace=Path(workspace), image=Path(image))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError, KeyError) as error:
            (root / "host-ipc-stop.json").write_text(json.dumps({
                "status": "STOP_DOCKER_BACKEND_IPC_RECEIPT",
                "error_class": type(error).__name__, "retry_performed": False,
            }, indent=2) + "\n", encoding="utf-8")
            raise RuntimeError("STOP_DOCKER_BACKEND_IPC_RECEIPT") from error
    from runtime.docker_schema_preflight_v1 import validate_model_response
    validation = validate_model_response(events, schema_path)
    (root / 'schema-validation.json').write_text(
        json.dumps(validation, indent=2) + '\n', encoding='utf-8')
    if validation['status'] != 'PASS':
        raise RuntimeError('STOP_DOCKER_BACKEND_OUTPUT:' + validation['status'])
    from integrated_efficiency_model_v1 import parse
    result = parse(root / "runner", contract)
    (root / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def preflight_schema(root: Path, schema: Path, instructions: Path,
                     workspace: Path) -> dict:
    with _host_repo_mapping_lock():
        return _preflight_schema_locked(root, schema, instructions, workspace)


def call(root: Path, prompt: str, image: Path, contract: str, workspace: Path):
    with _host_repo_mapping_lock():
        return _call_locked(root, prompt, image, contract, workspace)
