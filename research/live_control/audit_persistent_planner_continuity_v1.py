"""Audit the frozen two-turn persistent planner continuity probe."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/persistent-planner-continuity-live-01"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "persistent_planner_continuity_live_v1_prereg.json")
    result = read(ROOT / "result.json")
    rows = [json.loads(line) for line in (ROOT / "protocol.jsonl").read_text().splitlines()]
    for path, expected in plan["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    assert result["source_sha256"] == {
        Path(path).name: expected for path, expected in plan["source_sha256"].items()}
    sent = [row["message"] for row in rows if row["direction"] == "sent"]
    received = [row["message"] for row in rows if row["direction"] == "received"]
    starts = [row for row in sent if row.get("method") == "turn/start"]
    completed = [row for row in received if row.get("method") == "turn/completed"]
    usage = [row for row in received if row.get("method") == "thread/tokenUsage/updated"]
    interrupts = [row for row in sent if row.get("method") == "turn/interrupt"]
    startup = [row for row in received if row.get("method") == "mcpServer/startupStatus/updated"]
    assert len(starts) == len(completed) == len(usage) == 2
    assert not interrupts and not startup
    thread_ids = {row["params"]["threadId"] for row in starts + completed + usage}
    assert thread_ids == {result["thread_id"]}
    start_turn_ids = [row["result"]["turn"]["id"] for row in received
                      if row.get("id") in {item["id"] for item in starts}]
    completed_turn_ids = [row["params"]["turn"]["id"] for row in completed]
    usage_turn_ids = [row["params"]["turnId"] for row in usage]
    result_turn_ids = [row["handle"]["turn_id"] for row in result["turns"]]
    assert start_turn_ids == completed_turn_ids == usage_turn_ids == result_turn_ids
    assert len(set(result_turn_ids)) == 2
    assert starts[0]["params"]["input"][1]["type"] == "localImage"
    assert len(starts[1]["params"]["input"]) == 1
    assert all(row["params"]["outputSchema"] == {
        "type": "object", "properties": {"value": {"type": "string"}},
        "required": ["value"], "additionalProperties": False} for row in starts)
    assert result["status"] == "COMPLETED"
    assert result["same_thread"] and result["distinct_turn_ids"]
    assert result["context_recall_passed"]
    assert [row["answer"] for row in result["turns"]] == plan["expected_answers"]
    assert all(row["status"] == "completed" and row["answer_eligible"] and
               not row["cancellation_requested"] and
               row["completed_agent_messages"] == 1 for row in result["turns"])
    assert result["model_calls"] == plan["model_calls_max"] == 2
    latest = result["turns"][-1]["usage"]
    assert latest["total"] == {
        "totalTokens": 15583, "inputTokens": 15531, "cachedInputTokens": 6912,
        "cacheWriteInputTokens": 0, "outputTokens": 52, "reasoningOutputTokens": 18}
    audit = {
        "schema": "persistent-planner-continuity-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "thread_count": 1,
        "turn_count": 2,
        "distinct_turn_ids": 2,
        "context_recall_passed": True,
        "first_turn_local_images": 1,
        "second_turn_local_images": 0,
        "interrupts": 0,
        "mcp_startup_notifications": 0,
        "turn_elapsed_ms": result["turn_elapsed_ms"],
        "thread_start_ms": result["thread_start_ms"],
        "total_usage": latest["total"],
        "decision": "retain persistent typed thread continuity and proceed to a separately frozen live mid-generation invalidation test",
        "limits": "one two-turn nonce task on one host; no controller-loop, cancellation, semantic task quality, latency distribution or cross-machine claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
