"""Command-free transport probe; starts no model turn."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from codex_app_server_client_v1 import CodexAppServerClient


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
    with CodexAppServerClient(command, cwd=REPO) as client:
        initialized = client.initialize()
        models = client.request("model/list", {"includeHidden": False})
        started = client.start_thread(
            model="gpt-5.6-luna", cwd=str(REPO), approvalPolicy="never",
            sandbox={"type":"readOnly", "networkAccess":False},
            config={"project_doc_max_bytes": 0},
            baseInstructions="Return only the requested structured answer.",
            ephemeral=True, threadSource="exec")
    result = {
        "schema": "codex-app-server-command-free-probe-v1", "passed": True,
        "model_turns_started": 0, "model_calls": 0,
        "initialize_user_agent": initialized.get("userAgent"),
        "models_returned": len(models.get("data", [])),
        "requested_model_available": any(row.get("model") == "gpt-5.6-luna"
                                         for row in models.get("data", [])),
        "thread_id_present": bool(started.get("thread", {}).get("id")),
        "thread_ephemeral": started.get("thread", {}).get("ephemeral"),
        "resolved_model": started.get("model"),
        "command": command,
        "codex_version": subprocess.check_output([NODE, CLI, "--version"], text=True).strip(),
        "source_sha256": {Path(__file__).name: sha(__file__),
                          "codex_app_server_client_v1.py": sha(HERE / "codex_app_server_client_v1.py")},
        "scope": "transport, schema and ephemeral-thread creation only; no turn/start, model output, interruption or usage claim",
    }
    (root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
