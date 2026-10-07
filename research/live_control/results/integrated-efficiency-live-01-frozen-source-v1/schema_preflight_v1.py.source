"""Preflight one output schema through the same Codex CLI response-format path."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from jsonschema import Draft202012Validator, SchemaError

HERE = Path(__file__).resolve().parent
WINDOWS_PYTHON = Path("/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE_WSL = Path("/mnt/c/Program Files/nodejs/node.exe")
CLI_WSL = Path("/mnt/c/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js")
NODE_ARG = r"C:\Program Files\nodejs\node.exe"
CLI_ARG = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
RUNNER = HERE / "target_handle_model_runner_v2.py"
INSTRUCTIONS = HERE / "schema_preflight_responder_v1.txt"
MODEL = "gpt-5.6-luna"
EFFORT = "low"


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dump(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    os.replace(temporary, path)
def windows_path(path):
    return subprocess.run(["wslpath", "-w", str(Path(path).resolve())], capture_output=True,
                          text=True, check=True).stdout.strip()
def version(command):
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()


def compatibility_identity(schema):
    identity = {"schema_sha256": sha(schema), "requested_model": MODEL,
        "requested_effort": EFFORT, "runner_sha256": sha(RUNNER),
        "instructions_sha256": sha(INSTRUCTIONS), "cli_entry_sha256": sha(CLI_WSL),
        "cli_version": version([str(NODE_WSL), CLI_ARG, "--version"]),
        "node_version": version([str(NODE_WSL), "--version"]),
        "request_shape": "target_handle_model_runner_v2:handle:no-image:output-schema"}
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return identity, hashlib.sha256(encoded).hexdigest()


def local_schema_status(schema):
    try:
        value = json.loads(Path(schema).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(value)
        return "VALID", None
    except (json.JSONDecodeError, SchemaError) as error:
        return "INVALID", str(error)


def preflight(schema, cache_dir, result_dir, workspace):
    schema = Path(schema).resolve(); cache_dir = Path(cache_dir).resolve()
    result_dir = Path(result_dir).resolve(); workspace = Path(workspace).resolve()
    result_dir.mkdir(parents=True, exist_ok=False); cache_dir.mkdir(parents=True, exist_ok=True)
    local_status, local_error = local_schema_status(schema)
    identity, key = compatibility_identity(schema); cache_path = cache_dir / f"{key}.json"
    base = {"compatibility_key": key, "identity": identity, "schema": str(schema),
            "local_schema_status": local_status, "local_schema_error": local_error}
    if cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached["compatibility_key"] != key or cached["identity"] != identity:
            raise ValueError("cache identity mismatch")
        result = {**base, "cache_hit": True, "endpoint_status": cached["endpoint_status"],
            "endpoint_error": cached["endpoint_error"], "usage": None,
            "cached_first_observation": {"usage": cached["usage"], "elapsed_ms": cached["elapsed_ms"],
                "observed_at_unix_ns": cached["observed_at_unix_ns"]},
            "model_call_performed": False, "cost": None,
            "scope": "compatibility cache reuse; no fresh endpoint or semantic-quality claim"}
        dump(result_dir / "preflight-result.json", result); return result
    if local_status != "VALID":
        result = {**base, "cache_hit": False, "endpoint_status": "NOT_CALLED_LOCAL_SCHEMA_INVALID",
            "endpoint_error": local_error, "usage": None, "model_call_performed": False,
            "elapsed_ms": 0, "cost": None,
            "scope": "local schema refusal; endpoint compatibility unobserved"}
        cache_record = {**result, "observed_at_unix_ns": time.time_ns()}
        dump(cache_path, cache_record); dump(result_dir / "preflight-result.json", result); return result
    prompt = result_dir / "prompt.txt"
    prompt.write_text("Schema compatibility probe. Produce any object accepted by the supplied schema.",
                      encoding="utf-8", newline="\n")
    call = result_dir / "model-call"; started = time.perf_counter_ns()
    command = [str(WINDOWS_PYTHON), windows_path(RUNNER), NODE_ARG, CLI_ARG,
        windows_path(prompt), windows_path(workspace), windows_path(call), "handle", "-",
        windows_path(INSTRUCTIONS), windows_path(schema)]
    completed = subprocess.run(command, capture_output=True, timeout=90)
    elapsed_ms = (time.perf_counter_ns() - started) / 1e6
    (result_dir / "runner-stdout.txt").write_bytes(completed.stdout)
    (result_dir / "runner-stderr.txt").write_bytes(completed.stderr)
    events = [json.loads(line) for line in (call / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    failures = [row for row in events if row.get("type") in ("error", "turn.failed")]
    if completed.returncode == 0 and len(turns) == 1:
        endpoint_status, endpoint_error, usage = "ENDPOINT_COMPATIBLE", None, turns[0]["usage"]
    elif completed.returncode != 0 and failures:
        endpoint_status, endpoint_error, usage = "ENDPOINT_INCOMPATIBLE", failures[-1], None
    else:
        endpoint_status, endpoint_error, usage = "PREFLIGHT_FAILED", {"returncode": completed.returncode}, None
    result = {**base, "cache_hit": False, "endpoint_status": endpoint_status,
        "endpoint_error": endpoint_error, "usage": usage, "model_call_performed": True,
        "elapsed_ms": elapsed_ms, "cost": None,
        "scope": "actual no-GUI endpoint compatibility call; no semantic-quality or task claim"}
    cache_record = {**result, "observed_at_unix_ns": time.time_ns()}
    dump(cache_path, cache_record); dump(result_dir / "preflight-result.json", result); return result
