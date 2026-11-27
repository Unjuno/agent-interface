import json
from pathlib import Path
from research.live_control.codex_app_server_client_v2 import CodexAppServerClient

root = Path(__file__).resolve().parent / "raw" / "preflight"
result = {"preflight_id":"codex-appserver-linux-wsl-interop-initialize-20261021-r01"}
client = None
try:
    client = CodexAppServerClient(
        ["/mnt/c/Users/user/AppData/Local/OpenAI/Codex/bin/896a0166b774037a/codex.exe",
         "app-server", "--stdio"],
        journal_path=root / "protocol.jsonl")
    reply = client.initialize()
    result["status"] = "PASS_INITIALIZE_ONLY"
    result["server_info"] = reply.get("serverInfo")
    result["protocol_version"] = reply.get("protocolVersion")
except Exception as error:
    result.update(status="FAIL_INITIALIZE", error_type=type(error).__name__,
                  error=repr(error))
finally:
    if client is not None:
        try:
            client.close(timeout=5)
            result["client_close"] = "closed"
        except Exception as error:
            result["client_close"] = {"error_type":type(error).__name__,
                                      "error":repr(error)}
(root / "result.json").write_text(json.dumps(result, indent=2) + "\n",
                                  encoding="utf-8")
print(json.dumps(result, indent=2))