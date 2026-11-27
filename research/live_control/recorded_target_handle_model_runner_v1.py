"""Opt-in wrapper that records every existing integrated runner invocation.

Set AGENT_INTERFACE_MODEL_RUNNER to this file for a fresh evaluation run. Both
schema preflight and comparison calls use that shared runner seam. Each start
is fsynced before the unchanged target runner starts. A parent kill may leave
an unresolved attempt, which reconciliation must retain rather than count as
zero usage or success.
"""

from __future__ import annotations

import base64
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
TARGET_RUNNER = HERE / "target_handle_model_runner_v2.py"
LEDGER_MODULES = (HERE.parent / "integration" /
                  "standard_mcp_task_ledger_57_v1")
if str(LEDGER_MODULES) not in sys.path:
    sys.path.insert(0, str(LEDGER_MODULES))

from provider_attempt_recorder import ProviderAttemptRecorder


_ATTEMPT_ID = "integrated-target-runner-01"
_UNAVAILABLE_USAGE = {
    "status": "unavailable", "input_tokens": None, "output_tokens": None,
    "cached_input_tokens": None, "cache_write_input_tokens": None,
    "reasoning_output_tokens": None, "image_input_tokens": None,
}
_USAGE_FIELDS = (
    "cached_input_tokens", "cache_write_input_tokens",
    "reasoning_output_tokens", "image_input_tokens",
)


def _normalize_usage(raw):
    raw = raw if isinstance(raw, dict) else {}
    values = {}
    for name in ("input_tokens", "output_tokens", *_USAGE_FIELDS):
        value = raw.get(name)
        values[name] = value if type(value) is int and value >= 0 else None
    required = (values["input_tokens"], values["output_tokens"])
    status = ("reported" if all(value is not None for value in required) else
              "partial" if any(value is not None for value in required) else
              "unavailable")
    return dict(_UNAVAILABLE_USAGE) if status == "unavailable" else {
        "status": status, **values}


def _terminal_usage(event_bytes):
    try:
        events = [json.loads(line) for line in event_bytes.decode("utf-8").splitlines()
                  if line.strip()]
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False, dict(_UNAVAILABLE_USAGE)
    if not all(isinstance(row, dict) for row in events):
        return False, dict(_UNAVAILABLE_USAGE)
    terminal = [row for row in events if row.get("type") == "turn.completed"]
    if len(terminal) != 1:
        return False, dict(_UNAVAILABLE_USAGE)
    return True, _normalize_usage(terminal[0].get("usage"))


def _exception_status(error):
    if isinstance(error, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(error, KeyboardInterrupt):
        return "cancelled"
    return "failed"


def _bytes(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace")
    return b""


def _request_bytes(argv):
    if len(argv) != 9:
        raise ValueError("target runner expects exactly nine arguments")
    node, cli, prompt_name, working_name, output_name, mode, image_name, \
        instructions_name, schema_name = argv
    if mode not in ("coordinate", "handle"):
        raise ValueError("mode must be coordinate or handle")
    if mode == "coordinate" and image_name == "-":
        raise ValueError("coordinate mode requires an image")
    if mode == "handle" and image_name != "-":
        raise ValueError("handle mode must not receive an image")
    prompt = Path(prompt_name).read_bytes()
    image = None if image_name == "-" else Path(image_name).read_bytes()
    instructions = Path(instructions_name).read_bytes()
    schema = Path(schema_name).read_bytes()
    runner = TARGET_RUNNER.read_bytes()
    value = {
        "schema": "integrated_target_runner_request_v1",
        "attempt_scope": "one target_handle_model_runner subprocess invocation",
        "requested_model": "gpt-5.6-luna",
        "requested_effort": "low",
        "node": node,
        "cli": cli,
        "working_directory": str(Path(working_name).resolve()),
        "output_directory": str(Path(output_name).resolve()),
        "mode": mode,
        "prompt_base64": base64.b64encode(prompt).decode("ascii"),
        "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
        "image_base64": None if image is None else
            base64.b64encode(image).decode("ascii"),
        "image_sha256": None if image is None else hashlib.sha256(image).hexdigest(),
        "instructions_base64": base64.b64encode(instructions).decode("ascii"),
        "instructions_sha256": hashlib.sha256(instructions).hexdigest(),
        "schema_base64": base64.b64encode(schema).decode("ascii"),
        "schema_sha256": hashlib.sha256(schema).hexdigest(),
        "target_runner_sha256": hashlib.sha256(runner).hexdigest(),
        "recording_wrapper_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _response_bundle(output, stdout, stderr, error=None):
    output = Path(output)
    files = []
    if output.is_dir():
        for path in sorted(output.iterdir(), key=lambda value: value.name):
            if path.is_file():
                data = path.read_bytes()
                files.append({"name": path.name,
                              "sha256": hashlib.sha256(data).hexdigest(),
                              "bytes_base64": base64.b64encode(data).decode("ascii")})
    payload = {
        "schema": "integrated_target_runner_artifacts_v1",
        "files": files,
        "stdout_base64": base64.b64encode(stdout).decode("ascii"),
        "stderr_base64": base64.b64encode(stderr).decode("ascii"),
    }
    if error is not None:
        payload.update(exception_type=type(error).__name__, exception=str(error))
    return json.dumps(payload, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _publish_attempt_reference(output, ledger_root):
    output = Path(output)
    if not output.is_dir():
        return
    rows = [json.loads(line) for line in
            (ledger_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()]
    start = next(row for row in rows if row.get("event") == "model_attempt_started")
    terminal = next(row for row in rows if row.get("event") == "model_attempt_finished")
    complete = ProviderAttemptRecorder(ledger_root).reconcile()["complete"]
    reference = {
        "schema": "integrated_target_runner_attempt_ref_v1",
        "attempt_id": _ATTEMPT_ID,
        "status": terminal["status"],
        "ledger_relative_path": os.path.relpath(ledger_root, output),
        "journal_sha256": hashlib.sha256(
            (ledger_root / "attempts.jsonl").read_bytes()).hexdigest(),
        "request_ref": start["request_ref"],
        "response_ref": terminal["response_ref"],
        "usage": terminal["usage"],
        "journal_complete": complete,
    }
    temporary = output / "attempt-ledger-ref.json.tmp"
    target = output / "attempt-ledger-ref.json"
    temporary.write_text(json.dumps(reference, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8", newline="\n")
    os.replace(temporary, target)


def run_attempt(argv, *, delegate=None):
    """Record and run one target-runner process; return its normal CLI streams."""
    argv = list(argv)
    request = _request_bytes(argv)
    output = Path(argv[4]).resolve()
    ledger_root = output.parent / (output.name + ".attempt-ledger")
    recorder = ProviderAttemptRecorder(ledger_root)
    invoke_runner = delegate or _run_target
    captured = {}

    def invoke_once():
        try:
            completed = invoke_runner(argv)
        except BaseException as error:
            stdout = _bytes(getattr(error, "stdout", None))
            stderr = _bytes(getattr(error, "stderr", None))
            captured.update(error=error, returncode=(124 if isinstance(
                error, subprocess.TimeoutExpired) else 130 if isinstance(
                error, KeyboardInterrupt) else 1), stdout=stdout, stderr=stderr)
            events_path = output / "events.jsonl"
            event_bytes = events_path.read_bytes() if events_path.is_file() else b""
            _has_terminal, usage = _terminal_usage(event_bytes)
            return {
                "status": _exception_status(error),
                "usage": usage,
                "response_bytes": _response_bundle(output, stdout, stderr, error),
            }

        if not isinstance(completed, subprocess.CompletedProcess):
            error = RuntimeError("target runner delegate returned an invalid process result")
            captured.update(error=error, returncode=1, stdout=b"", stderr=b"")
            return {"status": "malformed", "usage": dict(_UNAVAILABLE_USAGE),
                    "response_bytes": _response_bundle(output, b"", b"", error)}

        stdout, stderr = _bytes(completed.stdout), _bytes(completed.stderr)
        captured.update(returncode=completed.returncode, stdout=stdout, stderr=stderr)
        events_path = output / "events.jsonl"
        events = events_path.read_bytes() if events_path.is_file() else b""
        has_terminal, usage = _terminal_usage(events)
        if completed.returncode == 0 and events and has_terminal:
            return {"status": "completed", "usage": usage,
                    "response_bytes": _response_bundle(output, stdout, stderr)}
        error = RuntimeError("integrated target runner exited without exactly one completed turn")
        captured["error"] = error
        return {"status": "failed" if completed.returncode else "malformed",
                "usage": usage,
                "response_bytes": _response_bundle(output, stdout, stderr, error)}

    recorded = recorder.invoke(_ATTEMPT_ID, request, invoke_once)
    _publish_attempt_reference(output, ledger_root)
    if "error" in captured:
        if isinstance(captured["error"], RuntimeError) and captured.get("returncode") == 0:
            return 1, captured["stdout"], captured["stderr"]
    if recorded.get("status") != "completed":
        return captured.get("returncode", 1), captured.get("stdout", b""), \
            captured.get("stderr", b"")
    return captured["returncode"], captured["stdout"], captured["stderr"]


def _run_target(argv):
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    target = importlib.import_module("target_handle_model_runner_v2")
    original_argv = sys.argv
    stdout, stderr = io.StringIO(), io.StringIO()
    try:
        sys.argv = [str(TARGET_RUNNER), *argv]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            returncode = target.main()
    finally:
        sys.argv = original_argv
    return subprocess.CompletedProcess(
        [sys.executable, str(TARGET_RUNNER), *argv], returncode,
        stdout.getvalue().encode("utf-8"), stderr.getvalue().encode("utf-8"))


def main(argv=None):
    code, stdout, stderr = run_attempt(sys.argv[1:] if argv is None else argv)
    sys.stdout.buffer.write(stdout)
    sys.stderr.buffer.write(stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
