"""Validate one frozen OpenTTD effect decision and complete token usage."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
RUNNER = HERE / "openttd_effect_model_runner_v1.py"
SCHEMA = HERE / "openttd_effect_decision_schema_v1.json"
INSTRUCTIONS = HERE / "openttd_effect_decision_responder_v1.txt"
USAGE = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")


def validate(value):
    required = {"format", "status", "next_action", "memory_use"}
    if type(value) is not dict or set(value) != required or value["format"] != "openttd-effect-decision-v1":
        raise ValueError("invalid effect decision")
    expected = {"observed": "advance_without_repeat", "uncertain": "inspect_without_mutation",
                "contradicted": "recover_without_repeat"}
    if value["status"] not in expected or value["next_action"] != expected[value["status"]]:
        raise ValueError("status/action conflict")
    if value["memory_use"] not in {"none", "supporting", "rejected_as_stale_or_misleading"}:
        raise ValueError("invalid memory use")
    return value


def parse(output):
    output = Path(output); rows = [json.loads(line) for line in (output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    messages = [row["item"]["text"] for row in rows if row.get("type") == "item.completed" and row.get("item", {}).get("type") == "agent_message"]
    turns = [row for row in rows if row.get("type") == "turn.completed"]
    threads = [row["thread_id"] for row in rows if row.get("type") == "thread.started"]
    if len(messages) != 1 or len(turns) != 1 or len(threads) != 1: raise ValueError("one completed turn required")
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
    command = [sys.executable, str(RUNNER), NODE, CLI, str(prompt_file), str(workspace),
               str(output), str(INSTRUCTIONS), str(SCHEMA), *map(str, images)]
    started = time.perf_counter_ns(); completed = subprocess.run(command, capture_output=True, timeout=90)
    (output.parent / f"{output.name}-stdout.txt").write_bytes(completed.stdout)
    (output.parent / f"{output.name}-stderr.txt").write_bytes(completed.stderr)
    if completed.returncode != 0: raise RuntimeError("model call failed; no retry")
    result = parse(output); result["caller_elapsed_ms"] = (time.perf_counter_ns() - started) / 1e6
    result["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest(); return result
