"""Two-turn live continuity probe for the persistent planner adapter."""
from dataclasses import asdict
import base64
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
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUB"
    "AScY42YAAAAASUVORK5CYII=")
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
    image = root / "observation.png"
    image.write_bytes(PNG_1X1)
    result = {
        "schema": "persistent-planner-continuity-probe-v1",
        "status": "STARTED",
        "model": "gpt-5.6-luna",
        "effort": "low",
        "model_calls_max": 2,
    }
    started_ns = time.perf_counter_ns()
    try:
        with CodexAppServerClient(
                command(), cwd=REPO, journal_path=root / "protocol.jsonl") as client:
            client.initialize()
            planner = PersistentPlannerAdapter(
                client, model="gpt-5.6-luna", effort="low", cwd=REPO,
                base_instructions=(
                    "Use no tools. Return only JSON matching the supplied schema. "
                    "Retain the conversation context within this thread."))
            thread_start_ns = time.perf_counter_ns()
            thread_id = planner.start_session()
            thread_ready_ns = time.perf_counter_ns()

            first_start_ns = time.perf_counter_ns()
            first_handle = planner.begin_turn(
                "The image is an inert transport fixture. Remember the nonce cobalt-seven "
                "for my next turn. Return {\"value\":\"stored\"}.",
                output_schema=SCHEMA, image_path=image.resolve())
            first = planner.await_turn(first_handle, timeout=120)
            first_end_ns = time.perf_counter_ns()

            second_start_ns = time.perf_counter_ns()
            second_handle = planner.begin_turn(
                "Return the nonce I asked you to remember in the previous turn as value.",
                output_schema=SCHEMA)
            second = planner.await_turn(second_handle, timeout=120)
            second_end_ns = time.perf_counter_ns()
            result.update({
                "status": "COMPLETED",
                "thread_id": thread_id,
                "same_thread": first_handle.thread_id == second_handle.thread_id == thread_id,
                "distinct_turn_ids": first_handle.turn_id != second_handle.turn_id,
                "thread_start_ms": (thread_ready_ns - thread_start_ns) / 1e6,
                "turn_elapsed_ms": [
                    (first_end_ns - first_start_ns) / 1e6,
                    (second_end_ns - second_start_ns) / 1e6,
                ],
                "turns": [asdict(first), asdict(second)],
                "expected_answers": [{"value": "stored"}, {"value": "cobalt-seven"}],
                "context_recall_passed": first.answer == {"value": "stored"} and
                                         second.answer == {"value": "cobalt-seven"},
                "model_calls": 2,
            })
    except Exception as error:
        result.update({"status": "FAILED", "error": repr(error)})
    result.update({
        "whole_process_ms": (time.perf_counter_ns() - started_ns) / 1e6,
        "codex_version": subprocess.check_output([NODE, CLI, "--version"], text=True).strip(),
        "source_sha256": {
            Path(__file__).name: sha(__file__),
            "persistent_planner_adapter_v1.py": sha(HERE / "persistent_planner_adapter_v1.py"),
            "codex_app_server_client_v2.py": sha(HERE / "codex_app_server_client_v2.py"),
        },
        "scope": "one same-host two-turn thread; structured continuity and accounting only",
    })
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    passed = (result["status"] == "COMPLETED" and result["same_thread"] and
              result["distinct_turn_ids"] and result["context_recall_passed"] and
              all(turn["answer_eligible"] for turn in result["turns"]))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
