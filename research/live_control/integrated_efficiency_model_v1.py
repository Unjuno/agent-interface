"""One image-backed Luna-low call for either fair comparison contract."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from compiled_form_grounding_v1 import validate as validate_compiled
from plain_form_points_v1 import validate as validate_plain
from model_call_backend_v1 import resolve as resolve_model_backend


HERE = Path(__file__).resolve().parent
WINDOWS_PYTHON = Path("/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
CONTRACTS = {
    "plain": (HERE / "plain_form_points_schema_v1.json",
              HERE / "plain_form_points_responder_v1.txt", validate_plain),
    "compiled": (HERE / "compiled_form_grounding_schema_v1.json",
                 HERE / "compiled_form_grounding_responder_v1.txt", validate_compiled),
}
RUNNER = Path(os.environ.get("AGENT_INTERFACE_MODEL_RUNNER",
                             str(HERE / "target_handle_model_runner_v2.py")))


# The legacy caller remains the default; explicit non-legacy backends fail closed.


def windows_path(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())],
                          capture_output=True, text=True, check=True).stdout.strip()


def parse(output: Path, contract: str):
    if contract not in CONTRACTS:
        raise ValueError("contract must be plain or compiled")
    events = [json.loads(line) for line in
              (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in events
                if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    threads = [row["thread_id"] for row in events if row.get("type") == "thread.started"]
    if len(messages) != 1 or len(turns) != 1 or len(threads) != 1:
        raise ValueError("one model thread, message and completed turn required")
    raw = json.loads(messages[0])
    normalized = CONTRACTS[contract][2](raw)
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    return {"raw": raw, "grounding": normalized, "usage": turns[0]["usage"],
            "call_id": threads[0],
            "runner_ns": process["exited_ns"] - process["started_ns"],
            "requested_model": process["requested_model"],
            "requested_effort": process["requested_effort"], "cost": None}


def _legacy_call(root: Path, prompt: str, image: Path, contract: str, workspace: Path):
    if contract not in CONTRACTS:
        raise ValueError("contract must be plain or compiled")
    schema, instructions, _validator = CONTRACTS[contract]
    root.mkdir(parents=True, exist_ok=False)
    prompt_path = root / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    output = root / "model"
    command = [str(WINDOWS_PYTHON), windows_path(RUNNER),
               NODE, CLI, windows_path(prompt_path), windows_path(workspace),
               windows_path(output), "coordinate", windows_path(image),
               windows_path(instructions), windows_path(schema)]
    completed = subprocess.run(command, capture_output=True, timeout=90)
    (root / "runner-stdout.txt").write_bytes(completed.stdout)
    (root / "runner-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError("grounding model call failed; no retry")
    result = parse(output, contract)
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
    return result


# Stable public boundary consumed by the integrated-efficiency runner.  The
# resolver keeps the legacy caller as the default while allowing an explicitly
# configured backend module to replace it fail-closed.
call = resolve(_legacy_call)
