"""Inject an inert MCP constructor into the pinned task-server entrypoint."""
from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from types import ModuleType

from mcp.server.fastmcp import FastMCP

REQUIRED_TOOLS = (
    "interface_close",
    "interface_dispatch",
    "interface_observe",
    "interface_recover_orphaned_input",
    "interface_results",
    "interface_verify_task",
)


def fake_create_server(targets, output_directory, *, session_mode,
                       supervised_win32_late_input_horizon_ns, supervised_win32_task_oracle):
    if (targets != {"fresh": 1} or session_mode != "supervised-win32"
            or supervised_win32_late_input_horizon_ns != 2_000_000_000
            or not callable(supervised_win32_task_oracle)):
        raise RuntimeError("offline task-server input mismatch")
    output = Path(output_directory)
    if output.name not in ("task-mcp", "followup-recovery-mcp") or not output.parent.name.startswith("trial-"):
        raise RuntimeError("offline task-server output path mismatch")
    output.mkdir()
    server = FastMCP("r02-offline-preflight")

    def refuse_all_calls() -> str:
        (output / "unexpected-tool-call").touch()
        raise RuntimeError("offline preflight only registers tools")

    for name in REQUIRED_TOOLS:
        server.add_tool(refuse_all_calls, name=name)
    (output / "registration.json").write_text(json.dumps({
        "backend": "inert-fastmcp", "optimization": sys.flags.optimize,
        "configured_session_mode": session_mode,
        "configured_horizon_ns": supervised_win32_late_input_horizon_ns,
        "configured_target": targets,
        "task_oracle_registered": True, "task_oracle_invoked": False,
    }), encoding="utf-8")
    return server


def main():
    if len(sys.argv) != 6:
        raise SystemExit("Expected pinned taskserver followed by targets, output, state and events paths.")
    taskserver, targets, output, state, events = map(Path, sys.argv[1:])
    packet = Path(__file__).resolve().parent
    trial = output.parent
    if (
        taskserver != packet / "task_oracle_server.py"
        or trial.parent != packet / "raw"
        or targets != trial / "targets.json"
        or state != trial / "fresh-task-target/fixture-state.json"
        or events != trial / "fresh-task-target/events.jsonl"
        or json.loads(state.read_text(encoding="utf-8")) != {"text": ""}
        or events.read_bytes()
    ):
        raise SystemExit("The offline invocation did not match the candidate task-server paths.")

    # Preload the only runtime import used by the exact R44 script.
    # The disposable repository root carries no native runtime.
    for name in ("runtime", "runtime.cli_v1", "runtime.cli_v1.mcp_server"):
        stub = ModuleType(name)
        stub.__path__ = []
        sys.modules[name] = stub
    sys.modules["runtime.cli_v1.mcp_server"].create_server = fake_create_server
    sys.argv = sys.argv[1:]
    runpy.run_path(str(taskserver), run_name="__main__")


if __name__ == "__main__":
    main()
