"""Independent checks over retained synthetic Win32 caller traces."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES = {
    "test_cancel_during_final_generation_read_sends_no_compensating_input.json": "closed_gate",
    "test_public_caller_backend_accept_before_return.json": "accepted",
    "test_public_caller_backend_block_before_acceptance.json": "blocked",
    "test_public_caller_backend_unretired_producer_stays_unknown.json": "stubborn",
}


def load_trace(path: Path) -> dict:
    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["scope"] == "synthetic_only", path
    assert row["producer_factory_calls"] == ["d" * 32], path
    action = row["result"]["action"]
    cancel = row["result"]["cancellation"]
    assert action["operation_id"] == "d" * 32, path
    assert action["target_generation"] == "c" * 64, path
    assert cancel["action_operation_id"] == action["operation_id"], path
    assert cancel["target_generation"] == action["target_generation"], path
    assert row["result"]["task_success"] is None, path
    assert row["result"]["task_effect"] is None, path
    return row


def check_case(row: dict, kind: str, path: Path) -> None:
    cancel = row["result"]["cancellation"]
    result = cancel["result"]
    events = [event["kind"] for event in row["events"]]
    assert row["producer_factory_calls"] == ["d" * 32], path
    assert cancel["replay_allowed"] is False, path
    assert cancel["task_success"] is None, path
    if kind in ("accepted", "blocked"):
        assert cancel["status"] == "recovered" and cancel["release_confirmed"] is True, path
        assert events.index("producer_exit_confirmed") < events.index("recovery_request"), path
        assert events.index("recovery_request") < events.index("recovery_up"), path
        assert events.index("recovery_up") < events.index("observer_request"), path
        if kind == "accepted":
            assert events.index("producer_down_accepted") < events.index("producer_exit_confirmed"), path
        else:
            assert "producer_down_accepted" not in events, path
    elif kind == "stubborn":
        assert cancel["status"] == "unknown" and cancel["release_confirmed"] is False, path
        assert "producer_down_accepted" in events, path
        assert not {"recovery_request", "recovery_up", "observer_request"}.intersection(events), path
    else:
        assert cancel["status"] == "unknown" and cancel["release_confirmed"] is False, path
        assert row["cancel_before_gate"] is True, path
        assert events == ["producer_exit_confirmed"], path
        assert result["producer_gate_state"] == "closed", path


def main() -> int:
    checked = 0
    for mode in ("normal", "optimized"):
        paths = sorted((ROOT / f"traces-{mode}").glob("*.json"))
        assert {path.name for path in paths} == set(CASES), mode
        for path in paths:
            row = load_trace(path)
            check_case(row, CASES[path.name], path)
            checked += 1
    print(f"PASS: {checked} traces; producer counts, target generations, recovery order, UNKNOWN retention")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
