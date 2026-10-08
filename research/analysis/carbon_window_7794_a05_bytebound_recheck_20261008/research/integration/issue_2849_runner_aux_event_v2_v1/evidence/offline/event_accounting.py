"""Fail-closed accounting for Codex JSONL events with known auxiliary warnings."""
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

KNOWN_WARNING = (
    "Skill descriptions were shortened to fit the 2% skills context budget. "
    "Codex can still see every skill, but some descriptions are shorter. "
    "Disable unused skills or plugins to leave more room for the rest."
)


def _reject_constant(value: str) -> None:
    raise ValueError("non-standard JSON constant: " + value)


def atomic_json_write(path: Path, value: dict) -> None:
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def account_events(events_path: Path) -> dict:
    try:
        rows = [json.loads(line, parse_constant=_reject_constant)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"status": "STOP_MALFORMED_EVENT_STREAM"}
    if any(not isinstance(row, dict) for row in rows):
        return {"status": "STOP_MALFORMED_EVENT_STREAM"}

    messages = []
    turns = []
    warnings = []
    for row in rows:
        kind = row.get("type")
        if kind in ("error", "turn.failed"):
            return {"status": "STOP_FAILURE_EVENT", "failure_type": kind}
        if kind == "item.completed":
            item = row.get("item")
            if not isinstance(item, dict):
                return {"status": "STOP_UNKNOWN_COMPLETED_ITEM"}
            item_type = item.get("type")
            if item_type == "agent_message":
                messages.append(item)
            elif item_type == "error" and item.get("message") == KNOWN_WARNING:
                warnings.append({"type": item_type,
                                 "message_sha256": hashlib.sha256(
                                     KNOWN_WARNING.encode("utf-8")).hexdigest(),
                                 "classification": "known_skills_context_budget_warning"})
            else:
                return {"status": "STOP_UNKNOWN_COMPLETED_ITEM",
                        "item_type": item_type}
        elif kind == "turn.completed":
            turns.append(row)
        elif kind in ("thread.started", "turn.started"):
            continue
        else:
            return {"status": "STOP_UNKNOWN_EVENT", "event_type": kind}

    if len(messages) != 1:
        return {"status": "STOP_ASSISTANT_MESSAGE_COUNT", "messages": len(messages)}
    if len(turns) != 1 or not isinstance(turns[0].get("usage"), dict):
        return {"status": "STOP_COMPLETED_TURN_OR_USAGE", "turns": len(turns)}
    usage = turns[0]["usage"]
    if not usage or any(not isinstance(value, int) or value < 0
                        for value in usage.values()):
        return {"status": "STOP_INVALID_USAGE", "turns": 1}
    response_text = messages[0].get("text")
    if not isinstance(response_text, str):
        return {"status": "STOP_MISSING_ASSISTANT_TEXT"}
    try:
        payload = json.loads(response_text, parse_constant=_reject_constant)
    except (json.JSONDecodeError, ValueError):
        return {"status": "STOP_INVALID_ASSISTANT_JSON"}
    return {"status": "PASS", "assistant_message_count": 1,
            "response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
            "response_is_object": isinstance(payload, dict),
            "turn_usage": usage, "auxiliary_items": warnings}


def main() -> int:
    _node, _legacy_cli, prompt_file, working, output, mode, image, instructions, schema = sys.argv[1:]
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    ipc = Path(os.environ.get("HOST_MODEL_IPC_DIR", "")).resolve()
    request_id = uuid.uuid4().hex
    image_path = None if image == "-" else Path(image).resolve()
    request = {"request_id": request_id, "mode": mode,
               "prompt": Path(prompt_file).read_text(encoding="utf-8"),
               "working": str(Path(working).resolve()),
               "image": None if image_path is None else str(image_path),
               "image_sha256": None if image_path is None else hashlib.sha256(image_path.read_bytes()).hexdigest(),
               "instructions": str(Path(instructions).resolve()),
               "instructions_sha256": hashlib.sha256(Path(instructions).read_bytes()).hexdigest(),
               "schema": str(Path(schema).resolve()),
               "schema_sha256": hashlib.sha256(Path(schema).read_bytes()).hexdigest(),
               "runner": "issue_2849_runner_aux_event_v2_v1", "authority_granted": False}
    (root / "prompt.txt").write_text(request["prompt"], encoding="utf-8")
    (root / "plan.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    started = time.perf_counter_ns()
    request_path = ipc / (request_id + ".request.json")
    response_path = ipc / (request_id + ".response.jsonl")
    atomic_json_write(request_path, request)
    deadline = time.monotonic() + float(os.environ.get("HOST_MODEL_IPC_TIMEOUT_S", "120"))
    while not response_path.exists():
        if time.monotonic() >= deadline:
            result = {"exit_code": 1, "status": "STOP_IPC_TIMEOUT",
                      "authority_granted": False, "request_id": request_id}
            (root / "process.json").write_text(json.dumps(result, indent=2) + "\n")
            return 1
        time.sleep(.05)
    shutil.copyfile(response_path, root / "events.jsonl")
    result = account_events(root / "events.jsonl")
    (root / "event-accounting.json").write_text(json.dumps(result, indent=2) + "\n")
    success = result["status"] == "PASS" and result["response_is_object"]
    receipt = {"exit_code": 0 if success else 1, "status": result["status"],
               "requested_model": "gpt-5.6-luna", "requested_effort": "low",
               "mode": mode, "boundary": "container-to-host-model-ipc",
               "authority_granted": False, "request_id": request_id,
               "started_ns": started, "exited_ns": time.perf_counter_ns(),
               "auxiliary_items": result.get("auxiliary_items", [])}
    (root / "process.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
