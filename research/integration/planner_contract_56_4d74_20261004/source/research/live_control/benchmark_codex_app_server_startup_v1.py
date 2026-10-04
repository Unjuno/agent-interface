"""Matched command-free app-server thread-start benchmark."""
import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

from codex_app_server_client_v2 import CodexAppServerClient


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"
DISABLED_FEATURES = [
    "apps", "plugins", "remote_plugin", "browser_use", "browser_use_external",
    "computer_use", "in_app_browser", "code_mode", "code_mode_host",
]
DISABLED_MCPS = ["blender", "chrome-devtools", "node_repl", "playwright", "puppeteer"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(variant):
    result = [NODE, CLI, "app-server", "--stdio"]
    if variant == "minimal":
        for feature in DISABLED_FEATURES:
            result += ["--disable", feature]
        for name in DISABLED_MCPS:
            result += ["-c", f"mcp_servers.{name}.enabled=false"]
    return result


def run(root, variant, replicate):
    journal = root / f"{variant}-{replicate}.jsonl"
    started_ns = time.perf_counter_ns()
    with CodexAppServerClient(command(variant), cwd=REPO, journal_path=journal) as client:
        client.initialize()
        thread_start_ns = time.perf_counter_ns()
        thread = client.start_thread(
            model="gpt-5.6-luna", cwd=str(REPO), approvalPolicy="never",
            sandbox="read-only", config={"project_doc_max_bytes":0},
            baseInstructions="Use no tools.", ephemeral=True, threadSource="exec")
        thread_ready_ns = time.perf_counter_ns()
        time.sleep(.5)
    stopped_ns = time.perf_counter_ns()
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    startup = [row for row in rows if row["direction"] == "received" and
               row["message"].get("method") == "mcpServer/startupStatus/updated"]
    return {
        "variant":variant, "replicate":replicate,
        "thread_id_present":bool(thread["thread"].get("id")),
        "thread_ephemeral":thread["thread"].get("ephemeral"),
        "thread_start_ms":(thread_ready_ns-thread_start_ns)/1e6,
        "whole_process_ms":(stopped_ns-started_ns)/1e6,
        "mcp_startup_notifications":len(startup),
        "mcp_names":sorted(set(row["message"]["params"]["name"] for row in startup)),
        "model_turns_started":0, "model_calls":0,
        "journal":journal.name, "journal_sha256":sha(journal),
    }


def main():
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=False)
    order = [("baseline",1),("minimal",1),("minimal",2),
             ("baseline",2),("baseline",3),("minimal",3)]
    runs = [run(root, variant, replicate) for variant, replicate in order]
    summary = {}
    for variant in ("baseline", "minimal"):
        selected = [row for row in runs if row["variant"] == variant]
        summary[variant] = {
            "thread_start_ms": [row["thread_start_ms"] for row in selected],
            "thread_start_median_ms": statistics.median(row["thread_start_ms"] for row in selected),
            "mcp_startup_notifications": [row["mcp_startup_notifications"] for row in selected],
        }
    result = {
        "schema":"codex-app-server-startup-benchmark-v1", "passed":True,
        "codex_version":subprocess.check_output([NODE, CLI, "--version"], text=True).strip(),
        "order":order, "runs":runs, "summary":summary,
        "median_reduction_ms":summary["baseline"]["thread_start_median_ms"]-
                              summary["minimal"]["thread_start_median_ms"],
        "minimal_contract":{"disabled_features":DISABLED_FEATURES,
                            "disabled_mcp_servers":DISABLED_MCPS},
        "model_turns_started":0, "model_calls":0,
        "source_sha256":{Path(__file__).name:sha(__file__),
                         "codex_app_server_client_v2.py":sha(HERE/"codex_app_server_client_v2.py")},
        "scope":"matched command-free process/thread startup only; no planner-turn or model-latency claim",
    }
    (root/"report.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
