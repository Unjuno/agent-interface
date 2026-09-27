"""Container-side model runner using a host-local Codex broker over a shared volume."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import uuid


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json_write(path: Path, value: dict, owner: tuple[int, int] | None = None) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if owner is not None:
            # Publish only after assigning the WSL broker's identity, while
            # retaining the request's owner-only permissions.
            os.chown(temporary, owner[0], owner[1])
            os.chmod(temporary, 0o600)
            metadata = temporary.stat()
            if (metadata.st_uid, metadata.st_gid) != owner or metadata.st_mode & 0o777 != 0o600:
                raise PermissionError("IPC request owner/mode verification failed")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ipc_owner_from_environment() -> tuple[int, int] | None:
    raw_uid = os.environ.get("HOST_MODEL_IPC_OWNER_UID")
    raw_gid = os.environ.get("HOST_MODEL_IPC_OWNER_GID")
    if raw_uid is None and raw_gid is None:
        return None
    if raw_uid is None or raw_gid is None:
        raise ValueError("HOST_MODEL_IPC_OWNER_UID and GID must be set together")
    try:
        uid, gid = int(raw_uid), int(raw_gid)
    except ValueError as exc:
        raise ValueError("HOST_MODEL_IPC_OWNER_UID/GID must be non-negative integers") from exc
    if uid < 0 or gid < 0:
        raise ValueError("HOST_MODEL_IPC_OWNER_UID/GID must be non-negative integers")
    return uid, gid


def main() -> int:
    _node, _legacy_cli, prompt_file, working, output, mode, image, instructions, schema = sys.argv[1:]
    if mode not in ("coordinate", "handle"):
        raise ValueError("mode must be coordinate or handle")
    root = Path(output).resolve(); root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    ipc = Path(os.environ.get("HOST_MODEL_IPC_DIR", "")).resolve()
    if not ipc.is_dir():
        raise RuntimeError("HOST_MODEL_IPC_DIR is missing or not a directory")
    ipc_owner = ipc_owner_from_environment()
    image_path = None if image == "-" else Path(image).resolve()
    request_id = uuid.uuid4().hex
    request = {"request_id": request_id, "mode": mode, "prompt": prompt,
               "working": str(Path(working).resolve()),
               "image": None if image_path is None else str(image_path),
               "image_sha256": None if image_path is None else sha(image_path),
               "instructions_b64": base64.b64encode(
                   Path(instructions).read_bytes()).decode("ascii"),
               "instructions_sha256": sha(Path(instructions)),
               "schema": str(Path(schema).resolve()), "schema_sha256": sha(Path(schema)),
               "runner": "container_host_model_ipc_runner_v1", "authority_granted": False}
    (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    plan = {key: value for key, value in request.items() if key != "instructions_b64"}
    plan["instructions_bytes"] = len(base64.b64decode(request["instructions_b64"]))
    (root / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
    request_path = ipc / f"{request_id}.request.json"
    response_path = ipc / f"{request_id}.response.jsonl"
    started_ns = time.perf_counter_ns()
    atomic_json_write(request_path, request, owner=ipc_owner)
    deadline = time.monotonic() + float(os.environ.get("HOST_MODEL_IPC_TIMEOUT_S", "120"))
    while not response_path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("host model IPC response timeout")
        time.sleep(.05)
    shutil.copyfile(response_path, root / "events.jsonl")
    lines = (root / "events.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines if line.strip()]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    messages = [row for row in events if row.get("type") == "item.completed"]
    if len(turns) != 1 or len(messages) != 1:
        raise RuntimeError("host model IPC response is not one completed turn/message")
    exited_ns = time.perf_counter_ns()
    result = {"exit_code": 0, "requested_model": "gpt-5.6-luna",
              "requested_effort": "low", "mode": mode,
              "boundary": "container-to-host-model-ipc", "authority_granted": False,
              "request_id": request_id, "started_ns": started_ns, "exited_ns": exited_ns}
    (root / "process.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
