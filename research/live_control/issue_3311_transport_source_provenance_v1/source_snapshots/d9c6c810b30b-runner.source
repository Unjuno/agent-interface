"""Container-side model runner using a host-local Codex broker over a shared volume."""
from __future__ import annotations

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


def atomic_json_write(path: Path, value: dict) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    _node, _legacy_cli, prompt_file, working, output, mode, image, instructions, schema = sys.argv[1:]
    if mode not in ("coordinate", "handle"):
        raise ValueError("mode must be coordinate or handle")
    root = Path(output).resolve(); root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    ipc = Path(os.environ.get("HOST_MODEL_IPC_DIR", "")).resolve()
    if not ipc.is_dir():
        raise RuntimeError("HOST_MODEL_IPC_DIR is missing or not a directory")
    image_path = None if image == "-" else Path(image).resolve()
    request_id = uuid.uuid4().hex
    request = {"request_id": request_id, "mode": mode, "prompt": prompt,
               "working": str(Path(working).resolve()),
               "image": None if image_path is None else str(image_path),
               "image_sha256": None if image_path is None else sha(image_path),
               "instructions": str(Path(instructions).resolve()),
               "instructions_sha256": sha(Path(instructions)),
               "schema": str(Path(schema).resolve()), "schema_sha256": sha(Path(schema)),
               "runner": "container_host_model_ipc_runner_v1", "authority_granted": False}
    (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    (root / "plan.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8", newline="\n")
    request_path = ipc / f"{request_id}.request.json"
    response_path = ipc / f"{request_id}.response.jsonl"
    started_ns = time.perf_counter_ns()
    atomic_json_write(request_path, request)
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
