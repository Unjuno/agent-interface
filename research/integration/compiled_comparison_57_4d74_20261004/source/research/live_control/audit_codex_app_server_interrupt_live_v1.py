"""Audit the frozen app-server interruption probe."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/codex-app-server-interrupt-live-01"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "codex_app_server_interrupt_live_v1_prereg.json")
    result = read(ROOT / "result.json")
    rows = [json.loads(line) for line in (ROOT / "protocol.jsonl").read_text().splitlines()]
    for path, expected in plan["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    assert result["source_sha256"] == {
        Path(path).name: expected for path, expected in plan["source_sha256"].items()}
    sent = [row for row in rows if row["direction"] == "sent"]
    received = [row for row in rows if row["direction"] == "received"]
    starts = [row for row in sent if row["message"].get("method") == "turn/start"]
    interrupts = [row for row in sent if row["message"].get("method") == "turn/interrupt"]
    turn_started = [row for row in received if row["message"].get("method") == "turn/started"]
    turn_completed = [row for row in received if row["message"].get("method") == "turn/completed"]
    usage = [row for row in received if row["message"].get("method") == "thread/tokenUsage/updated"]
    agent_items = [row for row in received if row["message"].get("method") == "item/completed" and
                   row["message"].get("params", {}).get("item", {}).get("type") == "agentMessage"]
    assert len(starts) == len(interrupts) == len(turn_started) == len(turn_completed) == 1
    assert turn_started[0]["observed_ns"] < interrupts[0]["observed_ns"]
    assert interrupts[0]["message"]["params"] == {
        "threadId": result["thread_id"], "turnId": result["turn_id"]}
    assert turn_completed[0]["message"]["params"]["turn"]["status"] == "interrupted"
    assert result["turn_completed_status"] == "interrupted"
    assert result["interrupt_ack"] == {} and result["interrupt_error"] is None
    assert result["completed_agent_messages"] == [] and result["answer_eligible"] is False
    assert not agent_items and not usage and result["turn_usage"] is None
    interrupt_ack = next(row for row in received if row["message"].get("id") ==
                         next(x["message"]["id"] for x in interrupts))
    metrics = {
        "turn_start_request_to_started_ms":
            (turn_started[0]["observed_ns"] - starts[0]["observed_ns"]) / 1e6,
        "interrupt_to_ack_ms":
            (interrupt_ack["observed_ns"] - interrupts[0]["observed_ns"]) / 1e6,
        "interrupt_to_completed_ms":
            (turn_completed[0]["observed_ns"] - interrupts[0]["observed_ns"]) / 1e6,
        "server_turn_duration_ms": result["turn_duration_ms"],
    }
    audit = {
        "schema":"codex-app-server-interrupt-live-audit-v1", "passed":True,
        "allocation_id":plan["allocation_id"], "turn_status":"interrupted",
        "interrupt_acknowledged":True, "agent_messages":0, "answer_eligible":False,
        "usage_notification":"absent_unknown_not_zero", "metrics":metrics,
        "mcp_startup_notifications":sum(
            row["message"].get("method") == "mcpServer/startupStatus/updated" for row in received),
        "decision":"retain app-server interruption as the planner cancellation boundary; add explicit absent-usage accounting and suppress unnecessary startup capabilities before controller integration",
        "limits":"one immediate interruption likely before model generation; no token-savings, mid-generation interruption, session-continuity, structured-answer or DOOM integration claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
