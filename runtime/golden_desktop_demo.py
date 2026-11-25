"""One entry point for the retained and live Agent Interface desktop demo.

Run this file inside Linux/WSL. It promotes the checked six-task fixture without
modifying the frozen comparison sources or evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path, PurePosixPath, PureWindowsPath


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "live_control"
RETAINED = RESEARCH / "results" / "integrated-efficiency-live-01"
RETAINED_SOURCE_ARCHIVE = RESEARCH / "results" / "integrated-efficiency-live-01-frozen-source-v1"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_text(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def unique_glob(pattern: str) -> Path | None:
    root = Path("/mnt/c/Users")
    matches = sorted(root.glob(pattern)) if root.is_dir() else []
    return matches[0] if len(matches) == 1 else None


def configured_path(env_name: str, default: Path | None) -> Path | None:
    raw = os.environ.get(env_name)
    return Path(raw).expanduser() if raw else default


def configuration() -> dict[str, Path | None]:
    windows_python = configured_path(
        "AGENT_INTERFACE_WINDOWS_PYTHON",
        unique_glob("*/AppData/Local/Programs/Python/Python*/python.exe"),
    )
    windows_node = configured_path(
        "AGENT_INTERFACE_WINDOWS_NODE", Path("/mnt/c/Program Files/nodejs/node.exe")
    )
    windows_cli = configured_path(
        "AGENT_INTERFACE_WINDOWS_CODEX_JS",
        unique_glob("*/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js"),
    )
    chrome_raw = os.environ.get("AGENT_INTERFACE_CHROMIUM")
    chrome = Path(chrome_raw) if chrome_raw else (
        Path(shutil.which("google-chrome")) if shutil.which("google-chrome") else None
    )
    native_key = "AGENT_INTERFACE_WINDOWS_CODEX_EXE"
    if native_key in os.environ:
        return {"windows_python": windows_python,
                "windows_codex_exe": Path(os.environ[native_key]).expanduser(),
                "chromium": chrome}
    return {
        "windows_python": windows_python,
        "windows_node": windows_node,
        "windows_cli": windows_cli,
        "chromium": chrome,
    }


def windows_arg(path: Path) -> str:
    completed = subprocess.run(
        ["wslpath", "-w", str(path)], capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def chromium_version(path: Path | None) -> str:
    if path is None or not path.is_file():
        raise ValueError("configure an existing Linux Chromium or Chrome executable")
    executable = path.resolve(strict=True)
    if (platform.system() != "Linux" or path.suffix.lower() == ".exe"
            or executable.suffix.lower() == ".exe" or not os.access(executable, os.X_OK)):
        raise ValueError("Golden requires an executable Linux Chromium or Chrome launcher")
    completed = subprocess.run([str(path), "--version"], capture_output=True,
                               text=True, timeout=10)
    detail = (completed.stdout or completed.stderr).strip()
    if completed.returncode != 0 or not any(name in detail for name in ("Chromium", "Chrome")):
        raise ValueError(f"Chromium --version could not start successfully (exit {completed.returncode}): {detail}")
    return detail


def doctor() -> dict:
    config = configuration()
    checks: list[dict] = []

    def add(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    add("linux", platform.system() == "Linux", platform.platform())
    add("wslpath", shutil.which("wslpath") is not None, shutil.which("wslpath"))
    add("display", bool(os.environ.get("DISPLAY")), os.environ.get("DISPLAY"))
    for module in ("PIL", "numpy", "Xlib", "jsonschema"):
        add("python:" + module, importlib.util.find_spec(module) is not None, module)
    for name, path in config.items():
        if name == "chromium":
            try:
                version = chromium_version(path)
            except (OSError, subprocess.SubprocessError, ValueError) as error:
                add(name, False, str(error))
            else:
                add(name, True, version)
            continue
        exists = path is not None and path.exists()
        if name == "windows_codex_exe":
            exists = (path is not None and path.is_absolute()
                      and path.suffix.lower() == ".exe" and path.is_file())
        add(name, exists, None if path is None else str(path))
    display_error = None
    try:
        from Xlib.display import Display

        connection = Display()
        connection.close()
        display_ok = True
    except Exception as error:
        display_ok = False
        display_error = f"{type(error).__name__}: {error}"
    add("x11_connection", display_ok, display_error or "connected")
    cli_version = None
    cli_ok = False
    native_codex = None
    try:
        if "windows_codex_exe" in config:
            from codex_app_server_client_v2 import wsl_codex_home_environment
            from schema_preflight_v1 import require_native_runner

            require_native_runner()
            executable = config["windows_codex_exe"]
            if not (executable.is_absolute() and executable.suffix.lower() == ".exe"
                    and executable.is_file()):
                raise ValueError("set AGENT_INTERFACE_WINDOWS_CODEX_EXE to an absolute WSL .exe file")
            environment = wsl_codex_home_environment(os.environ)
            if not Path(environment["CODEX_HOME"]).is_dir():
                raise ValueError("CODEX_HOME must be an existing directory visible to Windows")
            completed = subprocess.run([str(executable), "--version"], env=environment,
                                       capture_output=True, text=True, timeout=15)
            cli_ok = completed.returncode == 0 and completed.stdout.startswith("codex-cli ")
            cli_version = (completed.stdout or completed.stderr).strip()
            if cli_ok:
                native_codex = {"windows_path": windows_arg(executable.resolve()),
                                "version": cli_version, "executable_sha256": sha(executable)}
        elif config["windows_node"] and config["windows_cli"]:
            completed = subprocess.run(
                [str(config["windows_node"]), windows_arg(config["windows_cli"]), "--version"],
                capture_output=True, text=True, timeout=15,
            )
            cli_ok = completed.returncode == 0
            cli_version = (completed.stdout or completed.stderr).strip()
    except Exception as error:
        cli_ok = False
        cli_version = f"{type(error).__name__}: {error}"
    add("codex_cli", cli_ok, cli_version)
    result = {
        "schema": "agent_interface_golden_doctor_v1",
        "passed": all(row["passed"] for row in checks),
        "checks": checks,
        "configuration": {key: None if value is None else str(value)
                          for key, value in config.items()},
    }
    if native_codex is not None:
        result["native_codex"] = native_codex
    return result


def audit_retained() -> dict:
    plan = json.loads((RETAINED / "preregistration.json").read_text(encoding="utf-8"))
    report = json.loads((RETAINED / "report.json").read_text(encoding="utf-8"))
    audit = json.loads((RETAINED / "audit.json").read_text(encoding="utf-8"))
    expected_sources = plan.get("sources")
    source_mismatches = []
    source_manifest = None
    archived = {}
    if (not isinstance(expected_sources, dict) or not expected_sources
            or any(not isinstance(name, str) or not name or "/" in name or "\\" in name
                   or not isinstance(digest, str) or len(digest) != 64
                   or any(char not in "0123456789abcdef" for char in digest)
                   for name, digest in expected_sources.items())):
        source_mismatches.append("preregistration.sources")
        expected_sources = {}
    try:
        source_manifest = json.loads(
            (RETAINED_SOURCE_ARCHIVE / "SOURCE_MANIFEST.json").read_text(encoding="utf-8")
        )
        entries = source_manifest["files"]
        archived = {entry["name"]: entry for entry in entries}
        if (source_manifest.get("schema") != "integrated_efficiency_live_frozen_source_archive_v1"
                or source_manifest.get("study") != "integrated-efficiency-live-01"
                or source_manifest.get("source_count") != len(expected_sources)
                or not isinstance(source_manifest.get("source_commit"), str)
                or len(source_manifest["source_commit"]) != 40
                or any(char not in "0123456789abcdef" for char in source_manifest["source_commit"])
                or len(archived) != len(entries)
                or set(archived) != set(expected_sources)):
            source_mismatches.append("SOURCE_MANIFEST.json")
        else:
            for name, digest in expected_sources.items():
                entry = archived[name]
                archive_name = name + ".source"
                archive_path = RETAINED_SOURCE_ARCHIVE / archive_name
                if (entry.get("source_path") != f"research/live_control/{name}"
                        or entry.get("archive_file") != archive_name
                        or entry.get("sha256") != digest
                        or not archive_path.is_file()
                        or sha(archive_path) != digest
                        or archive_path.stat().st_size != entry.get("size_bytes")):
                    source_mismatches.append(name)
    except (OSError, AttributeError, KeyError, TypeError, json.JSONDecodeError):
        source_mismatches.append("SOURCE_MANIFEST.json")
    current_source_mismatches = []
    for name in expected_sources:
        current_path = RESEARCH / name
        archive_entry = (archived.get(name) if source_manifest is not None else None)
        archive_path = (RETAINED_SOURCE_ARCHIVE / archive_entry.get("archive_file")
                        if isinstance(archive_entry, dict)
                        and isinstance(archive_entry.get("archive_file"), str)
                        else None)
        if (not current_path.is_file() or archive_path is None or not archive_path.is_file()
                or normalized_text(current_path) != normalized_text(archive_path)):
            current_source_mismatches.append(name)
    evaluation = report["evaluation"]
    passed = (
        not source_mismatches
        and audit.get("passed") is True
        and evaluation.get("disposition") == "RETAIN"
        and all(evaluation["arms"][arm]["correct"] for arm in
                ("plain", "ephemeral", "persistent"))
        and evaluation.get("observed_break_even_task") == 2
    )
    return {
        "schema": "agent_interface_retained_demo_audit_v1",
        "passed": passed,
        "source_mismatches": source_mismatches,
        "source_validation": "frozen_archive",
        "frozen_source_commit": (source_manifest or {}).get("source_commit"),
        "frozen_source_count": (source_manifest or {}).get("source_count"),
        "current_source_mismatches": current_source_mismatches,
        "disposition": evaluation.get("disposition"),
        "exact_tasks": audit.get("exact_tasks"),
        "input_tokens": audit.get("final_input_tokens"),
        "planner_generations": {
            arm: evaluation["arms"][arm]["cumulative_planner_generations"][-1]
            for arm in ("plain", "ephemeral", "persistent")
        },
        "elapsed_ms": audit.get("elapsed_ms"),
        "observed_break_even_task": evaluation.get("observed_break_even_task"),
        "scope": plan["scope"],
    }


def read_json_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def verify_native_exec_argv(argv, model, effort):
    if (not all(type(argument) is str for argument in argv)
            or argv[-1:] != ["-"] or argv.count("--model") != 1
            or argv[argv.index("--model") + 1] != model
            or any(arg.startswith(("-m", "-i", "-p", "--model=", "--image", "--profile", "--config"))
                   or (arg.startswith("-c") and arg != "-c") for arg in argv[2:])):
        raise ValueError("Exec preflight must send the fixed model without an image or profile override")
    settings = {}
    for index, arg in enumerate(argv[:-1]):
        if arg == "-c":
            option = tomllib.loads(argv[index + 1])
            if len(option) != 1 or settings.keys() & option.keys():
                raise ValueError("Exec preflight has an ambiguous configuration option")
            settings.update(option)
    if (set(settings) != {"model_reasoning_effort", "model_instructions_file", "project_doc_max_bytes"}
            or settings["model_reasoning_effort"] != effort):
        raise ValueError("Exec preflight does not send the fixed reasoning effort")


def same_windows_path(left, right):
    # A WSL share can expose case-sensitive Linux path components.
    return left.anchor.casefold() == right.anchor.casefold() and left.parts[1:] == right.parts[1:]


def audit_launch_policy(out, report, preflight, preflight_root):
    from native_codex_usage_v1 import POLICY

    doctor_receipt = json.loads((out / "doctor.json").read_bytes())
    plan = json.loads((preflight_root / "model-call" / "plan.json").read_bytes())
    retained = json.loads((preflight_root / "preflight-result.json").read_bytes())
    identity = retained["identity"]
    cache_key = hashlib.sha256(canonical_json(identity).encode()).hexdigest()
    cache_path = out / "preflight" / "persistent" / "fresh-cache" / (cache_key + ".json")
    cached = json.loads(cache_path.read_bytes())
    cached.pop("observed_at_unix_ns", None)
    if (doctor_receipt.get("passed") is not True or retained.get("compatibility_key") != cache_key
            or canonical_json(preflight) != canonical_json(retained)
            or canonical_json(cached) != canonical_json(retained)):
        raise ValueError("doctor and preflight accounting receipts do not agree")
    config = doctor_receipt["configuration"]
    argv = plan["args"]
    launcher = report.get("environment", {}).get("configuration", {})
    raw_native = type(argv) is list and argv[1:2] == ["exec"]
    native = (raw_native or "windows_codex_exe" in config or "native_codex" in doctor_receipt
              or "windows_codex_exe" in launcher or "accounting_policy" in report
              or identity.get("cli_transport") == "windows-native-codex-exe"
              or "usage_policy" in identity or "cli_executable_sha256" in identity)
    if not native:
        if (type(argv) is not list or argv[2:3] != ["exec"]
                or not all(type(config.get(field)) is str and config[field]
                           for field in ("windows_node", "windows_cli"))
                or not identity.get("cli_entry_sha256") or not identity.get("node_version")
                or any(Path(config[field]).name.casefold() != PureWindowsPath(argument).name.casefold()
                       for field, argument in zip(("windows_node", "windows_cli"), argv[:2]))):
            raise ValueError("legacy launcher is not identified by the preflight receipts")
        return None
    if (not raw_native or type(config.get("windows_codex_exe")) is not str
            or not config["windows_codex_exe"] or "windows_node" in config or "windows_cli" in config
            or identity.get("cli_transport") != "windows-native-codex-exe"
            or identity.get("usage_policy") != POLICY or report.get("accounting_policy") != POLICY):
        raise ValueError("independent launch evidence requires matching native accounting")
    from schema_preflight_v1 import EFFORT, MODEL

    path = PureWindowsPath(argv[0])
    native_doctor = doctor_receipt["native_codex"]
    digest = identity["cli_executable_sha256"]
    if (not path.is_absolute() or path.suffix.lower() != ".exe"
            or path != PureWindowsPath(native_doctor["windows_path"])
            or path != PureWindowsPath(identity["cli_windows_path"])
            or type(digest) is not str or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or digest != native_doctor["executable_sha256"]
            or type(identity.get("cli_version")) is not str
            or not identity["cli_version"].startswith("codex-cli ")
            or identity["cli_version"] != native_doctor["version"]
            or plan.get("mode") != "handle" or plan.get("image_sha256") is not None
            or any(plan.get(field) != identity[field] for field in
                   ("requested_model", "requested_effort", "runner_sha256", "schema_sha256",
                    "instructions_sha256"))):
        raise ValueError("native executable or schema runner identity differs")
    if identity.get("requested_model") != MODEL or identity.get("requested_effort") != EFFORT:
        raise ValueError("native preflight differs from the fixed model or effort")
    verify_native_exec_argv(argv, MODEL, EFFORT)
    roots = doctor_receipt["native_run_root"]
    source_root = PurePosixPath(roots["wsl_path"])
    windows_root = PureWindowsPath(roots["windows_path"])
    if (not source_root.is_absolute() or ".." in source_root.parts
            or not windows_root.is_absolute() or ".." in windows_root.parts
            or report.get("environment", {}).get("native_run_root") != roots
            or argv.count("-C") != 1
            or not same_windows_path(PureWindowsPath(argv[argv.index("-C") + 1]),
                                     windows_root / "workspaces" / "persistent")):
        raise ValueError("native run roots disagree with the Exec workspace")
    return source_root, windows_root


def audit_grounding_results(out, tasks, thread_id, roots):
    from integrated_efficiency_app_server_model_v1 import per_turn_usage
    from native_codex_usage_v1 import normalize_usage

    source_root, windows_root = roots
    arm = out / "arms" / "persistent"
    details = json.loads((arm / "task-details.json").read_bytes())
    if len(details) != 6 or len(tasks) != 6:
        raise ValueError("six task source records are required")
    bound = {}
    for index, stage in ((0, "anchor"), (3, "repair")):
        task_id = f"task-{index + 1}"
        detail, task = details[index], tasks[index]
        trace = detail["trace"]
        if (task.get("task_id") != task_id or trace.get("task_id") != task_id
                or canonical_json(task["model_calls"]) != canonical_json(trace["model_calls"])):
            raise ValueError("grounding call is not bound to the expected task source")
        [call] = trace["model_calls"]
        call_id = call["call_id"]
        folder = out / "model-calls" / "persistent" / task_id / stage
        request = json.loads((folder / "request.json").read_bytes())
        returned = json.loads((folder / "result.json").read_bytes())
        source = PurePosixPath(detail["source"]["image"])
        relative = source.relative_to(source_root)
        provider = PureWindowsPath(request["provider_image"])
        retained_image = out.joinpath(*relative.parts).resolve()
        if (len(relative.parts) != 4 or relative.parts[:3] != ("arms", "persistent", "runtime")
                or source.suffix.lower() != ".png" or source != PurePosixPath(request["source_image"])
                or not same_windows_path(provider, windows_root.joinpath(*relative.parts))
                or not retained_image.is_relative_to(out.resolve())
                or sha(retained_image) != request.get("image_sha256")
                or returned.get("thread_id") != thread_id or returned.get("call_id") != call_id
                or returned.get("turn_status") != "completed" or call_id in bound):
            raise ValueError("grounding image or turn differs from the retained task source")
        acquired_usage = per_turn_usage(returned.get("provider_usage"), allow_missing_cache_write=True)
        if acquired_usage is None or acquired_usage != normalize_usage(returned.get("usage")):
            raise ValueError("grounding result usage differs from the acquired provider usage")
        bound[call_id] = (provider, returned["raw"], acquired_usage)
    if len({path for path, _answer, _usage in bound.values()}) != 2:
        raise ValueError("each grounding turn must use its own task source image")
    return bound


def verify_turn_input(params, model, effort):
    inputs = params.get("input")
    if (params.get("model") != model or params.get("effort") != effort
            or type(inputs) is not list or len(inputs) != 2
            or any(type(item) is not dict for item in inputs)
            or inputs[0].get("type") != "text" or type(inputs[0].get("text")) is not str
            or not inputs[0]["text"] or inputs[1].get("type") != "localImage"
            or type(inputs[1].get("path")) is not str
            or not PureWindowsPath(inputs[1]["path"]).is_absolute()):
        raise ValueError("grounding must send the fixed model and effort with text and one local image")
    return PureWindowsPath(inputs[1]["path"])


def verify_grounding_completion(params, answer):
    turn = params["turn"]
    items = turn.get("items")
    if (turn.get("status") != "completed" or turn.get("error") is not None
            or params.get("error") is not None or type(items) is not list):
        raise ValueError("grounding turn did not complete normally")
    messages = [item for item in items if item.get("type") == "agentMessage"]
    if (len(messages) != 1 or type(messages[0].get("text")) is not str
            or canonical_json(json.loads(messages[0]["text"])) != canonical_json(answer)):
        raise ValueError("completed grounding response differs from the recorded answer")


def audited_native_usage(out, report, preflight, preflight_events, task_calls, roots):
    from integrated_efficiency_app_server_model_v1 import per_turn_usage
    from native_codex_usage_v1 import accounting, normalize_usage, preflight_terminal

    preflight_usage = normalize_usage(preflight_terminal(preflight_events).get("usage"))
    if preflight_usage != normalize_usage(preflight.get("usage")):
        raise ValueError("raw schema preflight usage does not match the recorded result")
    model = preflight["identity"]["requested_model"]
    effort = preflight["identity"]["requested_effort"]
    if any(call.get("requested_model") != model or call.get("requested_effort") != effort
           for call in task_calls):
        raise ValueError("grounding usage records differ from the fixed model or effort")
    ids = [call["call_id"] for call in task_calls]
    thread_id = report.get("grounding_thread_id")
    if (len(ids) != 2 or len(set(ids)) != 2 or report.get("grounding_call_ids") != ids
            or type(thread_id) is not str or not thread_id):
        raise ValueError("two scoped raw grounding turns are required")
    bound_calls = audit_grounding_results(out, report["tasks"], thread_id, roots)
    protocol = read_json_lines(out / "persistent-grounding-app-server" / "protocol.jsonl")
    prepared = {}
    thread_sends = []
    turn_sends = []
    replies = {}
    sent_images = {}
    observed_usage = {}
    first_usage = {}
    completions = {}
    for index, row in enumerate(protocol):
        direction, message = row["direction"], row["message"]
        method = message.get("method")
        if direction == "send_uncertain":
            raise ValueError("uncertain App Server send")
        if direction in ("send_prepared", "sent") and method in ("thread/start", "turn/start"):
            params = message["params"]
            if type(message.get("id")) is not int:
                raise ValueError("App Server request has no valid request ID")
            rpc_id = message["id"]
            if method == "thread/start":
                if (params.get("model") != model
                        or params.get("config", {}).get("model_reasoning_effort") != effort):
                    raise ValueError("App Server thread does not request the fixed model and effort")
            else:
                if params.get("threadId") != thread_id:
                    raise ValueError("App Server request has no matching thread")
                image = verify_turn_input(params, model, effort)
                if direction == "sent":
                    sent_images[rpc_id] = image
            entry = (index, canonical_json(message))
            if direction == "send_prepared":
                if rpc_id in prepared:
                    raise ValueError("duplicate App Server send preparation")
                prepared[rpc_id] = entry
            else:
                sends = thread_sends if method == "thread/start" else turn_sends
                sends.append((rpc_id, entry))
        if direction != "received":
            continue
        if type(message.get("id")) is int:
            replies.setdefault(message["id"], []).append((index, message))
        if method == "thread/tokenUsage/updated":
            params = message["params"]
            turn_id = params["turnId"]
            if params["threadId"] != thread_id or turn_id not in ids:
                raise ValueError("unexpected raw grounding usage identity")
            first_usage.setdefault(turn_id, index)
            observed_usage[turn_id] = per_turn_usage(
                params.get("tokenUsage"), allow_missing_cache_write=True)
        if method == "turn/completed":
            params = message["params"]
            turn_id = params["turn"]["id"]
            if params["threadId"] != thread_id or turn_id not in ids or turn_id in completions:
                raise ValueError("invalid raw grounding completion")
            verify_grounding_completion(params, bound_calls[turn_id][1])
            completions[turn_id] = index
    sent_ids = {rpc_id for rpc_id, _entry in [*thread_sends, *turn_sends]}
    if (len(thread_sends) != 1 or len(turn_sends) != 2 or len(sent_ids) != 3
            or set(prepared) != sent_ids or set(completions) != set(ids)):
        raise ValueError("expected one prepared thread start and two prepared and completed grounding turns")

    def acknowledged(send):
        rpc_id, (send_index, request) = send
        prepare_index, prepared_request = prepared[rpc_id]
        if prepare_index >= send_index or prepared_request != request:
            raise ValueError("App Server send does not match its preparation")
        [(reply_index, reply)] = replies.get(rpc_id, [])
        if "error" in reply or reply_index <= send_index:
            raise ValueError("App Server acknowledgement is missing or precedes a matching send")
        return reply_index, reply["result"]

    thread_ack_index, thread = acknowledged(thread_sends[0])
    if (thread["thread"]["id"] != thread_id or thread.get("model") != model
            or thread.get("reasoningEffort") != effort):
        raise ValueError("App Server acknowledged a different thread, model or effort")
    previous_end = thread_ack_index
    for send, turn_id in zip(turn_sends, ids, strict=True):
        rpc_id, (send_index, _request) = send
        reply_index, reply = acknowledged(send)
        if (prepared[rpc_id][0] <= previous_end or reply["turn"]["id"] != turn_id
                or first_usage.get(turn_id, -1) <= send_index or completions[turn_id] <= send_index):
            raise ValueError("grounding turns lack serial sends and matching later notifications")
        if not same_windows_path(sent_images[rpc_id], bound_calls[turn_id][0]):
            raise ValueError("sent localImage differs from the independent task source")
        previous_end = max(reply_index, completions[turn_id])
    observed = [{"usage": preflight_usage}]
    for call in task_calls:
        usage = observed_usage.get(call["call_id"])
        if usage is None or usage != normalize_usage(call.get("usage")) or usage != bound_calls[call["call_id"]][2]:
            raise ValueError("grounding usage differs across the journal, result and recorded call")
        observed.append({"usage": usage})
    return accounting(observed)


def audit_live(out: Path) -> dict:
    report = json.loads((out / "golden-report.json").read_text(encoding="utf-8"))
    gate = json.loads((out / "preflight" / "persistent" / "gate" /
                       "gate-report.json").read_text(encoding="utf-8"))
    history = read_json_lines(out / "arms" / "persistent" / "runtime" /
                              "submission-history.jsonl")
    events = read_json_lines(out / "arms" / "persistent" / "runtime" / "events.jsonl")
    task_calls = [call for task in report["tasks"] for call in task["model_calls"]]
    preflight = gate["results"][0]["result"]
    call_ids = [call["call_id"] for call in task_calls]
    preflight_root = out / "preflight" / "persistent" / "gate" / "compiled-form-grounding"
    preflight_events = read_json_lines(preflight_root / "model-call" / "events.jsonl")
    call_ids.extend(row["thread_id"] for row in preflight_events
                    if row.get("type") == "thread.started")
    terminal = [row for row in events if row.get("event") == "terminal"]
    missing_old = [row for row in events if row.get("event") == "target_handle_checked"
                   and row.get("handle") == "persistent_a_field"
                   and row.get("status") == "MISSING" and row.get("eligible") is False]
    usage_fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                    "output_tokens", "reasoning_output_tokens")
    calls = [{"usage": preflight["usage"]}] + task_calls
    usage_error = None
    summary = None
    try:
        roots = audit_launch_policy(out, report, preflight, preflight_root)
        if roots is not None:
            process = json.loads((preflight_root / "model-call" / "process.json").read_bytes())
            if (preflight.get("endpoint_status") != "ENDPOINT_COMPATIBLE"
                    or type(process.get("exit_code")) is not int or process["exit_code"] != 0):
                raise ValueError("schema preflight has no successful raw process exit")
            summary = audited_native_usage(out, report, preflight, preflight_events, task_calls, roots)
        else:
            if any(type(call["usage"][field]) is not int or call["usage"][field] < 0
                   for call in calls for field in usage_fields):
                raise ValueError("legacy usage requires complete nonnegative token counts")
            recomputed_usage = {field: sum(call["usage"][field] for call in calls)
                                for field in usage_fields}
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        usage_error = str(error)
        summary = {"usage": {field: None for field in usage_fields},
                   "usage_coverage": {field: 0 for field in usage_fields},
                   "usage_status": "unverified"}
    if summary is None:
        usage_complete = True
        report_valid = report.get("passed") is True
    else:
        recomputed_usage = summary["usage"]
        usage_complete = summary["usage_status"] == "complete"
        report_valid = (usage_error is None and report.get("functional_passed") is True
                        and report.get("passed") is usage_complete
                        and all(canonical_json(report.get(field)) == canonical_json(value)
                                for field, value in summary.items()))
    expected_tasks = [f"task-{index}" for index in range(1, 7)]
    repair_succeeded = (len(report["tasks"]) > 3
                        and report["tasks"][3].get("repair", {}).get("succeeded") is True)
    functional_passed = all([
        report_valid,
        gate.get("accepted") is True,
        preflight.get("cache_hit") is False,
        preflight.get("model_call_performed") is True,
        len(call_ids) == 3 and len(set(call_ids)) == 3,
        report.get("planner_generations_including_preflight") == 3,
        report.get("model_visible_images") == 2,
        report.get("usage") == recomputed_usage,
        [row.get("task_id") for row in history] == expected_tasks,
        all(row.get("exact") is True for row in history),
        len(missing_old) == 1,
        report.get("old_target_pointer_admissions") == 0,
        len(terminal) > 0,
        all(row.get("release", {}).get("verified") is True
            and row["release"].get("keys_down") == []
            and row["release"].get("buttons_down") == [] for row in terminal),
        repair_succeeded,
        not (out / "failure.json").exists(),
    ])
    audit = {
        "schema": "agent_interface_golden_live_audit_v1",
        "passed": functional_passed and usage_complete,
        "output": display_path(out),
        "exact_tasks": len(history),
        "model_call_ids": call_ids,
        "usage": recomputed_usage,
        "terminal_programs": len(terminal),
        "verified_terminal_releases": sum(
            row.get("release", {}).get("verified") is True for row in terminal
        ),
        "old_layout_missing_checks": len(missing_old),
        "old_target_pointer_admissions": report.get("old_target_pointer_admissions"),
        "repair_succeeded": repair_succeeded,
        "scope": report["scope"],
    }
    if summary is not None:
        from native_codex_usage_v1 import POLICY

        audit.update(summary, accounting_policy=POLICY, functional_passed=functional_passed)
        if usage_error is not None:
            audit["usage_error"] = usage_error
    dump(out / "audit.json", audit)
    return audit


def configure_research_modules(config: dict[str, Path | None], chromium: Path):
    import integrated_efficiency_model_v1 as model
    import run_integrated_efficiency_live_v1 as implementation
    import schema_preflight_v1 as schema_preflight
    from integrated_efficiency_client_v1 import RuntimeClient

    windows_python = config["windows_python"]
    if windows_python is None:
        raise ValueError("Windows Python is required for the schema preflight runner")
    model.WINDOWS_PYTHON = windows_python
    schema_preflight.WINDOWS_PYTHON = windows_python
    schema_preflight.CLI_EXE_WSL = config.get("windows_codex_exe")
    if schema_preflight.CLI_EXE_WSL is None:
        windows_node = config["windows_node"]
        windows_cli = config["windows_cli"]
        if windows_node is None or windows_cli is None:
            raise ValueError("Windows Node and the Codex JavaScript entrypoint are required")
        model.NODE = windows_arg(windows_node)
        model.CLI = windows_arg(windows_cli)
        schema_preflight.NODE_WSL = windows_node
        schema_preflight.CLI_WSL = windows_cli
        schema_preflight.NODE_ARG = model.NODE
        schema_preflight.CLI_ARG = model.CLI

    class ConfiguredRuntimeClient(RuntimeClient):
        def start(self):
            from durable_submit_v4 import initialize
            from received_continuation_v1 import start
            from received_exchange_v2 import request_once

            self.root.mkdir(parents=True, exist_ok=False)
            self.errors = (self.root / "stderr.txt").open(
                "w", encoding="utf-8", newline="\n"
            )
            self.process = subprocess.Popen([
                sys.executable, "-u", str(RESEARCH / "integrated_efficiency_socket_v1.py"),
                "integrated-efficiency-chromium-v1", "serve", "--", "--app", "chromium",
                "--seed", str(self.seed), "--out", str(self.runtime),
                "--chromium", str(chromium),
            ], stdout=subprocess.PIPE, stderr=self.errors, text=True)
            self.temporary = tempfile.TemporaryDirectory(prefix="agent-interface-golden-")
            self.journal = Path(self.temporary.name) / "journal.jsonl"
            try:
                endpoint_line = self.process.stdout.readline()
                if not endpoint_line:
                    raise RuntimeError("runtime exited before publishing its private endpoint")
                self.endpoint = json.loads(endpoint_line)
                initial = request_once(self.endpoint["socket"], start(self.endpoint["socket"]),
                                       {"events": ["observation"], "timeout": 30})
                self.ready = next(row for row in initial["reply"]["records"]
                                  if row.get("event") == "ready")
                initialize(self.journal, initial["continuation"])
                return self
            except Exception:
                self.close()
                raise

    return implementation, ConfiguredRuntimeClient


def claim_output(out: Path, on_claimed) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to reuse output directory: {out}")
    out.mkdir(parents=True)
    if on_claimed is not None:
        on_claimed(out.lstat())


def run_live(out: Path, seed: int, *, on_output_claimed=None) -> dict:
    if "windows_codex_exe" in configuration():
        raise RuntimeError("the Windows native Codex bridge requires the Golden v2/v3 launcher")
    health = doctor()
    if not health["passed"]:
        raise RuntimeError("doctor failed; run the doctor command for exact missing dependencies")
    claim_output(out, on_output_claimed)
    dump(out / "doctor.json", health)
    config = configuration()
    chromium = config["chromium"]
    assert chromium is not None
    implementation, client_type = configure_research_modules(config, chromium)
    implementation.OUT = out
    implementation.RuntimeClient = client_type
    started = time.perf_counter_ns()
    preflight = implementation.preflight_call("persistent", "compiled")
    rows, independent = implementation.run_arm(
        "persistent", seed, out / "workspaces" / "persistent"
    )
    ended = time.perf_counter_ns()
    usage_fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                    "output_tokens", "reasoning_output_tokens")
    calls = [preflight] + [call for row in rows for call in row["model_calls"]]
    usage = {field: sum(call["usage"][field] for call in calls) for field in usage_fields}
    feedback_ms = [value / 1e6 for row in rows for value in row["input_feedback_ns"]]
    report = {
        "schema": "agent_interface_golden_desktop_live_v1",
        "passed": (
            independent.get("success") is True
            and len(rows) == 6
            and all(row["exact_submission"] and row["releases_verified"] for row in rows)
            and rows[3]["repair"] == {
                "required": True, "old_reference_status": "missing",
                "old_reference_pointer_admissions": 0,
                "attempted": True, "succeeded": True,
            }
        ),
        "seed": seed,
        "tasks_exact": sum(row["exact_submission"] for row in rows),
        "routes": [row["route"] for row in rows],
        "planner_generations_including_preflight": len(calls),
        "model_visible_images": sum(row["model_visible_images"] for row in rows),
        "usage": usage,
        "old_target_pointer_admissions": sum(row["old_target_pointer_admissions"] for row in rows),
        "all_releases_verified": all(row["releases_verified"] for row in rows),
        "input_feedback_median_ms": statistics.median(feedback_ms),
        "six_task_elapsed_ms": sum(row["elapsed_ns"] for row in rows) / 1e6,
        "whole_command_elapsed_ms": (ended - started) / 1e6,
        "independent_evaluation": independent,
        "tasks": rows,
        "environment": health,
        "scope": "one fresh persistent-only demonstration; no baseline comparison, rate, generality, or human-speed claim",
    }
    dump(out / "golden-report.json", report)
    return report


def default_output() -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    return ROOT / "artifacts-local" / ("golden-desktop-" + stamp)


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent Interface golden desktop demo")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="check Linux/X11, browser, Python and Codex dependencies")
    sub.add_parser("audit-retained", help="verify the frozen six-task comparison evidence")
    audit = sub.add_parser("audit-live", help="independently audit a fresh demo output")
    audit.add_argument("out", type=Path)
    live = sub.add_parser("run", help="run one fresh persistent six-task demonstration")
    live.add_argument("--out", type=Path, default=None)
    live.add_argument("--seed", type=int, default=991029)
    args = parser.parse_args()
    run_out = (args.out or default_output()).resolve() if args.command == "run" else None
    owned_out = None

    def record_claim(stat_result):
        nonlocal owned_out
        owned_out = stat_result

    try:
        if args.command == "doctor":
            result = doctor()
        elif args.command == "audit-retained":
            result = audit_retained()
        elif args.command == "audit-live":
            result = audit_live(args.out.resolve())
        else:
            result = run_live(run_out, args.seed, on_output_claimed=record_claim)
    except Exception as error:
        failure = {
            "schema": "agent_interface_golden_failure_v1",
            "passed": False,
            "error_type": type(error).__name__,
            "message": str(error),
            "output_retained": None if owned_out is None else display_path(run_out),
            "automatic_retry": False,
        }
        if owned_out is not None:
            try:
                if os.path.samestat(owned_out, run_out.lstat()):
                    with (run_out / "failure.json").open("x", encoding="utf-8", newline="\n") as stream:
                        stream.write(json.dumps(failure, indent=2) + "\n")
            except OSError:
                # Report the original failure even when evidence publication fails.
                pass
        print(json.dumps(failure, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
