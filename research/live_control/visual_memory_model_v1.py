"""Invoke and validate one frozen visual-memory target decision."""
import hashlib
import json
from pathlib import Path
import subprocess
import time


HERE = Path(__file__).resolve().parent
WINDOWS_PYTHON = Path("/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
RUNNER = HERE / "visual_memory_model_runner_v1.py"
SCHEMA = HERE / "visual_memory_decision_schema_v1.json"
INSTRUCTIONS = HERE / "visual_memory_decision_responder_v1.txt"
USAGE = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
         "output_tokens", "reasoning_output_tokens")


def windows_path(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())], capture_output=True,
                          text=True, check=True).stdout.strip()


def validate(value):
    required = {"format", "status", "x", "y", "reason", "memory_use"}
    if type(value) is not dict or set(value) != required or value["format"] != "visual-memory-target-decision-v1":
        raise ValueError("invalid decision fields")
    if value["memory_use"] not in {"none", "supporting", "rejected_as_stale_or_misleading"}:
        raise ValueError("invalid memory use")
    if value["status"] == "needs_decision":
        if value["x"] != 0 or value["y"] != 0 or value["reason"] not in {"ambiguous", "missing"}:
            raise ValueError("invalid abstention")
    elif (value["status"] != "target_reference" or value["reason"] != "matched"
          or type(value["x"]) is not int or type(value["y"]) is not int
          or not 0 <= value["x"] < 1280 or not 0 <= value["y"] < 800):
        raise ValueError("invalid target reference")
    return value


def parse(output):
    output = Path(output); events = [json.loads(line) for line in (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in events if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    threads = [row["thread_id"] for row in events if row.get("type") == "thread.started"]
    if len(messages) != 1 or len(turns) != 1 or len(threads) != 1: raise ValueError("one completed model turn required")
    usage = turns[0].get("usage")
    if type(usage) is not dict or any(type(usage.get(key)) is not int or usage[key] < 0 for key in USAGE):
        raise ValueError("complete usage required")
    process = json.loads((output / "process.json").read_text(encoding="utf-8"))
    if process["exit_code"] != 0: raise ValueError("successful process required")
    return {"call_id": threads[0], "decision": validate(json.loads(messages[0])), "usage": usage,
            "requested_model": process["requested_model"], "requested_effort": process["requested_effort"],
            "visible_images_submitted": process["visible_images_submitted"], "cost": None,
            "runner_ms": (process["exited_ns"] - process["started_ns"]) / 1e6}


def invoke(output, prompt, images, workspace):
    output = Path(output); prompt_file = output.parent / f"{output.name}-prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8", newline="\n")
    command = [str(WINDOWS_PYTHON), windows_path(RUNNER), NODE, CLI, windows_path(prompt_file),
               windows_path(workspace), windows_path(output), windows_path(INSTRUCTIONS), windows_path(SCHEMA)]
    command.extend(windows_path(path) for path in images)
    started = time.perf_counter_ns(); completed = subprocess.run(command, capture_output=True, timeout=90)
    (output.parent / f"{output.name}-stdout.txt").write_bytes(completed.stdout)
    (output.parent / f"{output.name}-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0: raise RuntimeError("model call failed; no retry")
    result = parse(output); result["caller_elapsed_ms"] = (time.perf_counter_ns() - started) / 1e6
    result["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
    return result
