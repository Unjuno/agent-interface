"""One-run supervised Win32 MCP server with a fixture-specific effect oracle."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

repo, targets_path, receipts_path, effect_path, oracle_log, oracle_id, token, events_path = sys.argv[1:]
sys.path.insert(0, repo)
from runtime.cli_v1.mcp_server import create_server

expected = {"saved": True, "text": token, "clicked": True}

def oracle(action):
    observed_ns = time.monotonic_ns()
    try:
        raw = Path(effect_path).read_bytes()
        actual = json.loads(raw.decode("utf-8"))
        events = [json.loads(line) for line in Path(events_path).read_text(encoding="utf-8").splitlines() if line.strip()]
        save_events = [event for event in events if event.get("kind") == "save"]
        save_event = save_events[0] if len(save_events) == 1 else None
        timing_valid = (isinstance(save_event, dict)
            and type(save_event.get("save_write_started_monotonic_ns")) is int
            and type(save_event.get("save_write_completed_monotonic_ns")) is int
            and save_event["save_write_started_monotonic_ns"] <= save_event["save_write_completed_monotonic_ns"] <= observed_ns)
        effect_match = actual == expected
        event_match = (save_event is not None and
            {k: save_event.get(k) for k in ("saved", "text", "clicked")} == expected)
        outcome = "success" if effect_match and event_match and timing_valid else "failure"
        reason = "exact_effect_and_timed_save_event_match" if outcome == "success" else "effect_event_or_timing_mismatch"
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raw = b""
        actual = None
        save_event = None
        events = []
        outcome = "failure"
        reason = type(exc).__name__
    evidence = {"schema": "win32-task-oracle-evidence-r01-v1",
        "oracle_id": oracle_id, "action": action, "expected": expected,
        "actual": actual, "save_event": save_event, "events": events,
        "outcome": outcome, "reason": reason,
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
