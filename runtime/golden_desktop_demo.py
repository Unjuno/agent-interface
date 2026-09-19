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
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "live_control"
RETAINED = RESEARCH / "results" / "integrated-efficiency-live-01"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        add(name, path is not None and path.exists(), None if path is None else str(path))
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
    if config["windows_node"] and config["windows_cli"]:
        try:
            completed = subprocess.run(
                [str(config["windows_node"]), windows_arg(config["windows_cli"]), "--version"],
                capture_output=True, text=True, timeout=15,
            )
            cli_ok = completed.returncode == 0
            cli_version = (completed.stdout or completed.stderr).strip()
        except Exception as error:
            cli_version = f"{type(error).__name__}: {error}"
    add("codex_cli", cli_ok, cli_version)
    return {
        "schema": "agent_interface_golden_doctor_v1",
        "passed": all(row["passed"] for row in checks),
        "checks": checks,
        "configuration": {key: None if value is None else str(value)
                          for key, value in config.items()},
    }


def audit_retained() -> dict:
    plan = json.loads((RETAINED / "preregistration.json").read_text(encoding="utf-8"))
    report = json.loads((RETAINED / "report.json").read_text(encoding="utf-8"))
    audit = json.loads((RETAINED / "audit.json").read_text(encoding="utf-8"))
    source_mismatches = [name for name, digest in plan["sources"].items()
                         if not (RESEARCH / name).is_file() or sha(RESEARCH / name) != digest]
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
    preflight_events = read_json_lines(
        out / "preflight" / "persistent" / "gate" / "compiled-form-grounding" /
        "model-call" / "events.jsonl"
    )
    call_ids.extend(row["thread_id"] for row in preflight_events
                    if row.get("type") == "thread.started")
    terminal = [row for row in events if row.get("event") == "terminal"]
    missing_old = [row for row in events if row.get("event") == "target_handle_checked"
                   and row.get("handle") == "persistent_a_field"
                   and row.get("status") == "MISSING" and row.get("eligible") is False]
    usage_fields = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                    "output_tokens", "reasoning_output_tokens")
    calls = [{"usage": preflight["usage"]}] + task_calls
    recomputed_usage = {field: sum(call["usage"][field] for call in calls)
                        for field in usage_fields}
    expected_tasks = [f"task-{index}" for index in range(1, 7)]
    passed = all([
        report.get("passed") is True,
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
        report["tasks"][3].get("repair", {}).get("succeeded") is True,
        not (out / "failure.json").exists(),
    ])
    audit = {
        "schema": "agent_interface_golden_live_audit_v1",
        "passed": passed,
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
        "repair_succeeded": report["tasks"][3].get("repair", {}).get("succeeded"),
        "scope": report["scope"],
    }
    dump(out / "audit.json", audit)
    return audit


def configure_research_modules(config: dict[str, Path | None], chromium: Path):
    import integrated_efficiency_model_v1 as model
    import run_integrated_efficiency_live_v1 as implementation
    import schema_preflight_v1 as schema_preflight
    from integrated_efficiency_client_v1 import RuntimeClient

    windows_python = config["windows_python"]
    windows_node = config["windows_node"]
    windows_cli = config["windows_cli"]
    assert windows_python and windows_node and windows_cli
    model.WINDOWS_PYTHON = windows_python
    model.NODE = windows_arg(windows_node)
    model.CLI = windows_arg(windows_cli)
    schema_preflight.WINDOWS_PYTHON = windows_python
    schema_preflight.NODE_WSL = windows_node
    schema_preflight.CLI_WSL = windows_cli
    schema_preflight.NODE_ARG = windows_arg(windows_node)
    schema_preflight.CLI_ARG = windows_arg(windows_cli)

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


def run_live(out: Path, seed: int) -> dict:
    health = doctor()
    if not health["passed"]:
        raise RuntimeError("doctor failed; run the doctor command for exact missing dependencies")
    if out.exists():
        raise FileExistsError(f"refusing to reuse output directory: {out}")
    out.mkdir(parents=True)
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
    try:
        if args.command == "doctor":
            result = doctor()
        elif args.command == "audit-retained":
            result = audit_retained()
        elif args.command == "audit-live":
            result = audit_live(args.out.resolve())
        else:
            result = run_live(run_out, args.seed)
    except Exception as error:
        failure = {
            "schema": "agent_interface_golden_failure_v1",
            "passed": False,
            "error_type": type(error).__name__,
            "message": str(error),
            "output_retained": None if run_out is None else display_path(run_out),
            "automatic_retry": False,
        }
        if run_out is not None and run_out.is_dir():
            dump(run_out / "failure.json", failure)
        print(json.dumps(failure, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
