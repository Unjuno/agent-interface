"""Audit the frozen post-delta planner interruption probe."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/persistent-planner-mid-generation-interrupt-live-01"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "persistent_planner_mid_generation_interrupt_live_v1_prereg.json")
    result = read(ROOT / "result.json")
    rows = [json.loads(line) for line in (ROOT / "protocol.jsonl").read_text().splitlines()]
    for path, expected in plan["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    assert result["source_sha256"] == {
        Path(path).name: expected for path, expected in plan["source_sha256"].items()}
    sent = [row for row in rows if row["direction"] == "sent"]
    received = [row for row in rows if row["direction"] == "received"]
    starts = [row for row in sent if row["message"].get("method") == "turn/start"]
    deltas = [row for row in received
              if row["message"].get("method") == plan["trigger_method"]]
    interrupts = [row for row in sent if row["message"].get("method") == "turn/interrupt"]
    completed = [row for row in received if row["message"].get("method") == "turn/completed"]
    usage = [row for row in received if row["message"].get("method") == "thread/tokenUsage/updated"]
    agent_completed = [row for row in received
                       if row["message"].get("method") == "item/completed" and
                       row["message"].get("params", {}).get("item", {}).get("type") == "agentMessage"]
    assert len(starts) == len(deltas) == len(interrupts) == len(completed) == 1
    assert not usage and not agent_completed
    identity = {result["thread_id"], result["turn_id"]}
    for row in (deltas[0], interrupts[0]):
        assert {row["message"]["params"]["threadId"],
                row["message"]["params"]["turnId"]} == identity
    assert deltas[0]["message"]["params"]["delta"] == '{"'
    assert deltas[0]["observed_ns"] < interrupts[0]["observed_ns"] < completed[0]["observed_ns"]
    interrupt_id = interrupts[0]["message"]["id"]
    ack = next(row for row in received if row["message"].get("id") == interrupt_id)
    assert ack["message"]["result"] == {}
    assert completed[0]["message"]["params"]["turn"]["status"] == "interrupted"
    assert result["interrupt"] == {"outcome": "requested", "response": {}}
    assert result["turn"]["status"] == "interrupted"
    assert result["turn"]["cancellation_requested"] is True
    assert result["turn"]["answer_eligible"] is False
    assert result["turn"]["answer"] is None
    assert result["turn"]["usage"] is None
    assert result["model_calls"] == plan["model_calls_max"] == 1
    assert result["interrupts"] == plan["interrupts_max"] == 1
    metrics = {
        "delta_observed_to_interrupt_sent_ms":
            (interrupts[0]["observed_ns"] - deltas[0]["observed_ns"]) / 1e6,
        "interrupt_sent_to_ack_ms":
            (ack["observed_ns"] - interrupts[0]["observed_ns"]) / 1e6,
        "interrupt_sent_to_completed_ms":
            (completed[0]["observed_ns"] - interrupts[0]["observed_ns"]) / 1e6,
        "server_turn_duration_ms": completed[0]["message"]["params"]["turn"]["durationMs"],
    }
    audit = {
        "schema": "persistent-planner-mid-generation-interrupt-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "delta_chars_before_interrupt": len(deltas[0]["message"]["params"]["delta"]),
        "interrupt_acknowledged": True,
        "turn_status": "interrupted",
        "completed_agent_messages": 0,
        "answer_eligible": False,
        "usage_notification": "absent_unknown_not_zero",
        "metrics": metrics,
        "decision": "integrate the typed interrupt boundary with event-driven observation invalidation in a new controller version",
        "limits": "one deliberately long text turn; no token-savings, repeated-race, controller-loop, GUI-task or cross-machine claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
