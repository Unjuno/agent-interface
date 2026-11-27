"""One-run supervised Win32 MCP server with a fixture-specific effect oracle."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

repo, targets_path, receipts_path, effect_path, oracle_log, oracle_id, token = sys.argv[1:]
sys.path.insert(0, repo)
from runtime.cli_v1.mcp_server import create_server

expected = {"saved": True, "text": token, "clicked": True}

def oracle(action):
    oracle_read_started_ns = time.monotonic_ns()
    try:
        raw = Path(effect_path).read_bytes()
        actual = json.loads(raw.decode("utf-8"))
        outcome = "success" if actual == expected else "failure"
        reason = "exact_effect_match" if outcome == "success" else "effect_mismatch"
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raw = b""
        actual = None
        outcome = "failure"
        reason = type(exc).__name__
    oracle_read_returned_ns = time.monotonic_ns()
    observed_ns = oracle_read_returned_ns
    evidence = {"schema": "win32-task-oracle-evidence-r50-v1",
        "effect_read_started_monotonic_ns": oracle_read_started_ns,
        "effect_read_returned_monotonic_ns": oracle_read_returned_ns,
        "oracle_id": oracle_id, "action": action, "expected": expected,
        "actual": actual, "outcome": outcome, "reason": reason,
        "observed_monotonic_ns": observed_ns,
        "effect_sha256": __import__("hashlib").sha256(raw).hexdigest()}
    Path(oracle_log).write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"call_id": action["call_id"], "operation_id": action["operation_id"],
        "target_generation": action["target_generation"], "oracle_id": oracle_id,
        "outcome": outcome, "observed_monotonic_ns": observed_ns,
        "evidence_ref": str(Path(oracle_log).resolve())}

def main():
    server = create_server(json.loads(Path(targets_path).read_text(encoding="utf-8")),
        receipts_path, session_mode="supervised-win32",
        supervised_win32_task_oracle=oracle)
    server.run(transport="stdio")

if __name__ == "__main__":
    main()
