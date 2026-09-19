"""Model-free initialization check for the MAP01 v26 planner transport."""
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "live_control"))

from codex_app_server_client_v2 import CodexAppServerClient
from map01_overlap_controller_v26 import REPO, app_server_command


def main():
    with CodexAppServerClient(app_server_command(), cwd=REPO) as client:
        result = client.initialize()
    print(json.dumps({
        "schema": "map01_v26_app_server_diagnostic_v1",
        "passed": isinstance(result, dict),
        "initialize_result_keys": sorted(result) if isinstance(result, dict) else [],
        "model_turns": 0,
    }, indent=2))
    return 0 if isinstance(result, dict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
