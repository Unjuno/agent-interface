"""One bounded app-server turn interruption probe."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from codex_app_server_client_v2 import AppServerError, CodexAppServerClient


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NODE = r"C:\Program Files\nodejs\node.exe"
CLI = r"C:\Users\junny\AppData\Roaming\npm\node_modules\@openai\codex\bin\codex.js"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=False)
    command = [NODE, CLI, "app-server", "--stdio"]
    result = {"schema":"codex-app-server-interrupt-probe-v1", "status":"STARTED",
              "command":command, "model":"gpt-5.6-luna", "effort":"low"}
    try:
        with CodexAppServerClient(command, cwd=REPO, journal_path=root / "protocol.jsonl") as client:
            initialized = client.initialize()
            thread = client.start_thread(
                model="gpt-5.6-luna", cwd=str(REPO), approvalPolicy="never",
                sandbox="read-only", config={"project_doc_max_bytes":0},
                baseInstructions="Use no tools. Return only the requested JSON.",
                ephemeral=True, threadSource="exec")
            thread_id = thread["thread"]["id"]
            turn = client.start_turn(thread_id, [{
                "type":"text", "text":"Return {\"answer\":\"ready\"} only.",
                "text_elements":[],
            }], model="gpt-5.6-luna", effort="low", outputSchema={
                "type":"object", "properties":{"answer":{"type":"string"}},
                "required":["answer"], "additionalProperties":False,
            })
            turn_id = turn["turn"]["id"]
            started = client.wait_notification(
                lambda row: row.get("method") == "turn/started" and
                row.get("params", {}).get("threadId") == thread_id and
                row.get("params", {}).get("turn", {}).get("id") == turn_id,
                timeout=30)
            interrupt_sent_ns = time.perf_counter_ns()
            interrupt_error = None
            try:
                interrupt_ack = client.interrupt_turn(thread_id, turn_id)
            except AppServerError as error:
                interrupt_ack = None
                interrupt_error = str(error)
            completed = client.wait_turn_completed(thread_id, turn_id, timeout=60)
            usage = client.latest_turn_usage(thread_id, turn_id)
            turn_items = completed["turn"].get("items", [])
            result.update({
                "status":"COMPLETED", "initialize_user_agent":initialized.get("userAgent"),
                "thread_id":thread_id, "thread_ephemeral":thread["thread"].get("ephemeral"),
                "turn_id":turn_id, "turn_started_status":started["params"]["turn"]["status"],
                "interrupt_sent_ns":interrupt_sent_ns, "interrupt_ack":interrupt_ack,
                "interrupt_error":interrupt_error,
                "turn_completed_status":completed["turn"]["status"],
                "turn_duration_ms":completed["turn"].get("durationMs"),
                "turn_usage":usage,
                "completed_agent_messages":[row for row in turn_items
                                            if row.get("type") == "agentMessage"],
                "answer_eligible":completed["turn"]["status"] == "completed" and
                                  any(row.get("type") == "agentMessage" for row in turn_items),
            })
    except Exception as error:
        result.update({"status":"FAILED", "error":repr(error)})
    result.update({
        "codex_version":subprocess.check_output([NODE, CLI, "--version"], text=True).strip(),
        "source_sha256":{Path(__file__).name:sha(__file__),
                         "codex_app_server_client_v2.py":sha(HERE / "codex_app_server_client_v2.py")},
        "scope":"one frozen no-tool turn; interruption mechanics and accounting only",
    })
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
