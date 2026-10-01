"""Host-IPC response runner with assistant-only counting and image binding."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import uuid


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
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


def inspect_response(raw: bytes) -> tuple[list[dict], dict]:
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("event rows must be JSON objects")
    completed = [row.get("item") for row in rows if row.get("type") == "item.completed"
                 and isinstance(row.get("item"), dict)]
    assistants = [item for item in completed if item.get("type") == "agent_message"]
    auxiliary = [item for item in completed if item.get("type") == "error"]
    turns = [row for row in rows if row.get("type") == "turn.completed"]
    threads = [row for row in rows if row.get("type") == "thread.started"]
    if len(threads) != 1 or len(turns) != 1 or not isinstance(turns[0].get("usage"), dict):
        raise ValueError("expected one thread and one completed turn with usage")
    if len(assistants) != 1:
        raise ValueError("expected exactly one completed assistant message")
    text = assistants[0].get("text")
    if not isinstance(text, str) or not isinstance(json.loads(text), dict):
        raise ValueError("expected one assistant JSON object")
    return rows, {"thread_id": threads[0].get("thread_id"), "turn_count": 1,
                  "assistant_message_count": 1, "auxiliary_error_count": len(auxiliary),
                  "auxiliary_error_types": [item.get("type") for item in auxiliary],
                  "usage": turns[0]["usage"], "assistant_json_sha256": sha_bytes(text.encode())}


def main() -> int:
    _node, _legacy_cli, prompt_file, working, output, mode, image, instructions, schema = __import__("sys").argv[1:]
    if mode not in ("handle", "coordinate") or (mode == "handle") != (image == "-"):
        raise ValueError("mode/image contract mismatch")
    root = Path(output).resolve(); root.mkdir(parents=True, exist_ok=False)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    ipc = Path(os.environ.get("HOST_MODEL_IPC_DIR", "")).resolve()
    if not ipc.is_dir():
        raise RuntimeError("HOST_MODEL_IPC_DIR missing")
    instruction_path, schema_path = Path(instructions).resolve(), Path(schema).resolve()
    image_path = None if image == "-" else Path(image).resolve()
    if image_path is not None and not image_path.is_file():
        raise FileNotFoundError(image_path)
    started_ns = time.perf_counter_ns()
    request_id = uuid.uuid4().hex
    request = {"request_id": request_id, "mode": mode, "prompt": prompt,
               "working": str(Path(working).resolve()),
               "image": None if image_path is None else str(image_path),
               "image_sha256": None if image_path is None else sha_bytes(image_path.read_bytes()),
               "instructions": str(instruction_path),
               "instructions_sha256": sha_bytes(instruction_path.read_bytes()),
               "schema": str(schema_path), "schema_sha256": sha_bytes(schema_path.read_bytes()),
               "runner": "container_host_model_ipc_runner_v3", "authority_granted": False}
    (root / "prompt.txt").write_text(prompt, encoding="utf-8", newline="\n")
    (root / "plan.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    request_path = ipc / f"{request_id}.request.json"
    response_path = ipc / f"{request_id}.response.jsonl"
    atomic_json(request_path, request)
    deadline = time.monotonic() + float(os.environ.get("HOST_MODEL_IPC_TIMEOUT_S", "120"))
    while not response_path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("host model IPC response timeout")
        time.sleep(.05)
    raw = response_path.read_bytes()
    (root / "events.jsonl").write_bytes(raw)
    _rows, accounting = inspect_response(raw)
    exited_ns = time.perf_counter_ns()
    process = {"exit_code": 0, "requested_model": "gpt-5.6-luna",
        "requested_effort": "low", "mode": mode,
        "boundary": "container-to-host-model-ipc", "authority_granted": False,
        "request_id": request_id, "started_ns": started_ns, "exited_ns": exited_ns,
        "raw_event_sha256": sha_bytes(raw), **accounting}
    (root / "process.json").write_text(json.dumps(process, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_RUNNER_V3", "request_id": request_id,
                      "mode": mode, "image_sha256": request["image_sha256"],
                      "assistant_message_count": accounting["assistant_message_count"],
                      "auxiliary_error_count": accounting["auxiliary_error_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
