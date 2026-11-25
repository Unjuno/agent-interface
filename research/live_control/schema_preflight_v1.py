"""Preflight one output schema through the same Codex CLI response-format path."""
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from jsonschema import Draft202012Validator, SchemaError

try:
    from .codex_app_server_client_v2 import wsl_codex_home_environment
    from .native_codex_usage_v1 import CACHE_WRITE, POLICY, normalize_usage, preflight_terminal
    from .native_preflight_job_v1 import RECEIPT, START_RECORD, LeaseWriter, completed_receipt
except ImportError:
    from codex_app_server_client_v2 import wsl_codex_home_environment
    from native_codex_usage_v1 import CACHE_WRITE, POLICY, normalize_usage, preflight_terminal
    from native_preflight_job_v1 import RECEIPT, START_RECORD, LeaseWriter, completed_receipt

HERE = Path(__file__).resolve().parent
WINDOWS_PYTHON = Path("/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe")
NODE_WSL = Path("/mnt/c/Program Files/nodejs/node.exe")
CLI_WSL = Path("/mnt/c/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js")
NODE_ARG = r"C:\Program Files\nodejs\node.exe"
CLI_ARG = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
DEFAULT_RUNNER = HERE / "target_handle_model_runner_v2.py"
NATIVE_OWNER = HERE / "native_preflight_job_v1.py"
APP_SERVER_OWNER = HERE / "native_app_server_job_v1.py"
RUNNER = Path(os.environ.get("AGENT_INTERFACE_MODEL_RUNNER", str(DEFAULT_RUNNER)))
CLI_EXE_WSL = None
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
def version(command, **options):
    return subprocess.run(command, capture_output=True, text=True, check=True,
                          **options).stdout.strip()


def require_native_runner():
    if RUNNER.resolve() != DEFAULT_RUNNER.resolve():
        raise ValueError("native Codex requires the built-in schema preflight runner")


def compatibility_identity(schema):
    identity = {"schema_sha256": sha(schema), "requested_model": MODEL,
        "requested_effort": EFFORT, "runner_sha256": sha(RUNNER),
        "instructions_sha256": sha(INSTRUCTIONS),
        "request_shape": f"{RUNNER.name}:handle:no-image:output-schema"}
    if CLI_EXE_WSL is None:
        identity.update(cli_entry_sha256=sha(CLI_WSL),
                        cli_version=version([str(NODE_WSL), CLI_ARG, "--version"]),
                        node_version=version([str(NODE_WSL), "--version"]))
    else:
        require_native_runner()
        identity.update(cli_transport="windows-native-codex-exe", usage_policy=POLICY,
                        cli_windows_path=windows_path(CLI_EXE_WSL),
                        windows_owner_sha256=sha(NATIVE_OWNER),
                        windows_app_server_owner_sha256=sha(APP_SERVER_OWNER),
                        cli_executable_sha256=sha(CLI_EXE_WSL),
                        cli_version=version([str(CLI_EXE_WSL), "--version"], timeout=15,
                            env=wsl_codex_home_environment(os.environ)))
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
    launch_options = {}
    owner_start = None
    outer_timeout = False
    with (LeaseWriter(result_dir) if CLI_EXE_WSL is not None else nullcontext()) as lease:
        if lease is not None:
            owner_start = {"run_nonce": lease.nonce, "owner_sha256": identity["windows_owner_sha256"]}
            dump(result_dir / START_RECORD, owner_start)
            command = [str(WINDOWS_PYTHON), windows_path(NATIVE_OWNER), windows_path(result_dir),
                       lease.nonce, windows_path(RUNNER), "--native-codex-exe", identity["cli_windows_path"]]
            launch_options["env"] = wsl_codex_home_environment(os.environ)
        else:
            command = [str(WINDOWS_PYTHON), windows_path(RUNNER), NODE_ARG, CLI_ARG]
        command += [windows_path(prompt), windows_path(workspace), windows_path(call), "handle", "-",
                    windows_path(INSTRUCTIONS), windows_path(schema)]
        try:
            completed = subprocess.run(command, capture_output=True, timeout=90, **launch_options)
        except subprocess.TimeoutExpired as error:
            if lease is None:
                raise
            outer_timeout = True
            completed = subprocess.CompletedProcess(command, None, error.stdout or b"", error.stderr or b"")
    elapsed_ms = (time.perf_counter_ns() - started) / 1e6
    (result_dir / "runner-stdout.txt").write_bytes(completed.stdout)
    (result_dir / "runner-stderr.txt").write_bytes(completed.stderr)
    ownership = None
    if CLI_EXE_WSL is not None:
        try:
            ownership = json.loads((result_dir / RECEIPT).read_bytes())
        except (OSError, ValueError):
            pass
        if outer_timeout or not completed_receipt(ownership, completed.returncode, **owner_start):
            result = {**base, "cache_hit": False, "endpoint_status": "PREFLIGHT_JOB_UNVERIFIED",
                      "endpoint_error": {"outer_timeout": outer_timeout, "returncode": completed.returncode},
                      "usage": None, "usage_status": "unverified", "model_call_performed": None,
                      "elapsed_ms": elapsed_ms, "cost": None, "windows_job": ownership,
                      "scope": "native schema preflight did not establish completed Windows job custody"}
            dump(result_dir / "preflight-result.json", result)
            return result
    events = [json.loads(line) for line in (call / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    turns = [row for row in events if row.get("type") == "turn.completed"]
    failures = [row for row in events if row.get("type") in ("error", "turn.failed")]
    if completed.returncode == 0 and len(turns) == 1 and (CLI_EXE_WSL is None or not failures):
        endpoint_status, endpoint_error = "ENDPOINT_COMPATIBLE", None
        usage = turns[0]["usage"] if CLI_EXE_WSL is None else turns[0].get("usage")
        if CLI_EXE_WSL is not None:
            try:
                preflight_terminal(events)
            except ValueError as error:
                endpoint_status = "PREFLIGHT_LIFECYCLE_UNVERIFIED"
                endpoint_error = {"reason": str(error)}
                usage = None
            else:
                try:
                    usage = normalize_usage(usage)
                except ValueError as error:
                    endpoint_status = "PREFLIGHT_USAGE_UNVERIFIED"
                    endpoint_error = {"reason": str(error)}
                    usage = None
    elif failures and (completed.returncode != 0 or CLI_EXE_WSL is not None):
        endpoint_status, endpoint_error, usage = "ENDPOINT_INCOMPATIBLE", failures[-1], None
    else:
        endpoint_status, endpoint_error, usage = "PREFLIGHT_FAILED", {"returncode": completed.returncode}, None
    result = {**base, "cache_hit": False, "endpoint_status": endpoint_status,
        "endpoint_error": endpoint_error, "usage": usage, "model_call_performed": True,
        "elapsed_ms": elapsed_ms, "cost": None,
        "scope": "actual no-GUI endpoint compatibility call; no semantic-quality or task claim"}
    if CLI_EXE_WSL is not None:
        result["windows_job"] = ownership
        result["usage_status"] = ("unverified" if usage is None else
                                  "complete" if CACHE_WRITE in usage else "partial")
    cache_record = {**result, "observed_at_unix_ns": time.time_ns()}
    dump(cache_path, cache_record); dump(result_dir / "preflight-result.json", result); return result
