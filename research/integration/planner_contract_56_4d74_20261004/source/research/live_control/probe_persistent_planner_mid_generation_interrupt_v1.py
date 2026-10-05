"""Interrupt one persistent planner turn after its first answer delta."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from codex_app_server_client_v2 import CodexAppServerClient
from persistent_planner_adapter_v1 import PersistentPlannerAdapter


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
DISABLED_FEATURES = [
    "apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
    "computer_use", "in_app_browser", "code_mode", "code_mode_host",
]
DISABLED_MCPS = ["blender", "chrome-devtools", "node_repl", "playwright", "puppeteer"]
SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "string"}},
    "required": ["value"],
    "additionalProperties": False,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command():
    result = [NODE, CLI, "app-server", "--stdio"]
    for feature in DISABLED_FEATURES:
        result += ["--disable", feature]
    for name in DISABLED_MCPS:
        result += ["-c", f"mcp_servers.{name}.enabled=false"]
    return result


def main():
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": "persistent-planner-mid-generation-interrupt-probe-v1",
        "status": "STARTED",
        "model": "gpt-5.6-luna",
        "effort": "low",
        "model_calls_max": 1,
        "interrupts_max": 1,
        "trigger_method": "item/agentMessage/delta",
    }
    try:
        with CodexAppServerClient(
                command(), cwd=REPO, journal_path=root / "protocol.jsonl") as client:
            client.initialize()
            planner = PersistentPlannerAdapter(
                client, model="gpt-5.6-luna", effort="low", cwd=REPO,
                base_instructions="Use no tools. Return only JSON matching the schema.")
            planner.start_session()
            handle = planner.begin_turn(
                "Return a JSON object whose value is a detailed self-contained technical "
                "essay of at least 2500 words about reliable event-driven GUI control.",
                output_schema=SCHEMA)
            delta = client.wait_notification(
                lambda row: row.get("method") == "item/agentMessage/delta" and
                row.get("params", {}).get("threadId") == handle.thread_id and
                row.get("params", {}).get("turnId") == handle.turn_id,
                timeout=120)
            trigger_ns = time.perf_counter_ns()
            interrupt = planner.interrupt(handle)
            interrupt_returned_ns = time.perf_counter_ns()
            turn = planner.await_turn(handle, timeout=120)
            completed_ns = time.perf_counter_ns()
            result.update({
                "status": "COMPLETED",
                "thread_id": handle.thread_id,
                "turn_id": handle.turn_id,
                "delta_item_id": delta.get("params", {}).get("itemId"),
                "delta_chars": len(delta.get("params", {}).get("delta", "")),
                "interrupt": interrupt,
                "trigger_to_interrupt_return_ms":
                    (interrupt_returned_ns - trigger_ns) / 1e6,
                "trigger_to_turn_completed_ms": (completed_ns - trigger_ns) / 1e6,
                "turn": asdict(turn),
                "model_calls": 1,
                "interrupts": 1,
            })
    except Exception as error:
        result.update({"status": "FAILED", "error": repr(error)})
    result.update({
        "codex_version": subprocess.check_output([NODE, CLI, "--version"], text=True).strip(),
        "source_sha256": {
            Path(__file__).name: sha(__file__),
            "persistent_planner_adapter_v1.py": sha(HERE / "persistent_planner_adapter_v1.py"),
            "codex_app_server_client_v2.py": sha(HERE / "codex_app_server_client_v2.py"),
        },
        "scope": "one same-host turn interrupted after its first matching agent-message delta",
    })
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    passed = (result["status"] == "COMPLETED" and
              result["turn"]["cancellation_requested"] and
              not result["turn"]["answer_eligible"] and
              result["model_calls"] == result["interrupts"] == 1)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
