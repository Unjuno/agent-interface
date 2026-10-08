"""Independently audit the retained persistent desktop v3 allocation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULT = HERE / "results/golden-desktop-app-server-v3-live-01"
TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens")
CAMEL = {
    "input_tokens": "inputTokens",
    "cached_input_tokens": "cachedInputTokens",
    "cache_write_input_tokens": "cacheWriteInputTokens",
    "output_tokens": "outputTokens",
    "reasoning_output_tokens": "reasoningOutputTokens",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def methods(rows, direction):
    return Counter(row["message"].get("method") for row in rows
                   if row["direction"] == direction)


def main():
    plan = read(HERE / "golden_desktop_app_server_v3_live_v1_prereg.json")
    for path, expected in plan["source_sha256"].items():
        assert sha(ROOT / path) == expected, path

    manifest = read(RESULT / "retention-manifest.json")
    assert manifest["allocation_id"] == plan["allocation_id"]
    assert manifest["excluded_derived_files"] == ["retention-manifest.json", "app-server-audit.json"]
    assert manifest["total_files"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(row["bytes"] for row in manifest["files"])
    for row in manifest["files"]:
        path = RESULT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], row["path"]
    actual = {path.relative_to(RESULT).as_posix() for path in RESULT.rglob("*") if path.is_file()}
    expected = {row["path"] for row in manifest["files"]} | set(manifest["excluded_derived_files"])
    assert actual == expected

    report = read(RESULT / "golden-report.json")
    assert report["passed"] and report["tasks_exact"] == plan["tasks"] == 6
    assert report["routes"] == plan["routes"]
    assert report["planner_generations_including_preflight"] == 3
    assert report["model_visible_images"] == 2
    assert report["old_target_pointer_admissions"] == 0
    assert report["all_releases_verified"] is True
    assert report["grounding_turns"] == 2
    assert len(set(report["grounding_call_ids"])) == 2
    assert report["environment"]["passed"] is True
    assert len(report["environment"]["checks"]) == 15
    assert all(row["passed"] for row in report["environment"]["checks"])
    versions = {row["name"]: row["detail"] for row in report["environment"]["checks"]}
    assert versions["python:openpyxl"] == "3.1.2"
    assert versions["python:et_xmlfile"] == "1.1.0"
    assert report["independent_evaluation"]["success"] is True
    assert report["independent_evaluation"]["record_count"] == 6
    assert all(value == 1 for value in report["independent_evaluation"]["exact_counts"].values())
    assert report["tasks"][3]["repair"] == {
        "required": True, "old_reference_status": "missing",
        "old_reference_pointer_admissions": 0, "attempted": True,
        "succeeded": True}

    live_audit = read(RESULT / "audit.json")
    assert live_audit["passed"] is True
    assert live_audit["terminal_programs"] == 57
    assert live_audit["verified_terminal_releases"] == 57
    assert live_audit["old_target_pointer_admissions"] == 0
    assert live_audit["repair_succeeded"] is True

    gate = read(RESULT / "preflight/persistent/gate/gate-report.json")
    assert gate["accepted"] and gate["model_calls"] == gate["fresh_usage_records"] == 1
    preflight_usage = gate["results"][0]["result"]["usage"]

    protocol = [json.loads(line) for line in
                (RESULT / "persistent-grounding-app-server/protocol.jsonl").read_text().splitlines()]
    sent, received = methods(protocol, "sent"), methods(protocol, "received")
    assert sent["initialize"] == sent["initialized"] == sent["thread/start"] == 1
    assert sent["turn/start"] == 2
    assert received["thread/started"] == 1
    assert received["turn/started"] == received["turn/completed"] == 2
    assert received["thread/tokenUsage/updated"] == 2
    assert sum(count for name, count in received.items() if name and "mcp" in name.lower()) == 0

    started = [row["message"]["params"] for row in protocol
               if row["direction"] == "received" and row["message"].get("method") == "turn/started"]
    completed = [row["message"]["params"] for row in protocol
                 if row["direction"] == "received" and row["message"].get("method") == "turn/completed"]
    assert {row["turn"]["id"] for row in started} == set(report["grounding_call_ids"])
    assert {row["turn"]["id"] for row in completed} == set(report["grounding_call_ids"])
    assert all(row["threadId"] == report["grounding_thread_id"] for row in started + completed)
    assert all(row["turn"]["status"] == "completed" for row in completed)

    grounding_usage = [row["message"]["params"]["tokenUsage"]["last"] for row in protocol
                       if row["direction"] == "received" and
                       row["message"].get("method") == "thread/tokenUsage/updated"]
    reconciled = {field: preflight_usage[field] +
                  sum(row[CAMEL[field]] for row in grounding_usage)
                  for field in TOKEN_FIELDS}
    assert reconciled == report["usage"] == live_audit["usage"]
    all_ids = set(live_audit["model_call_ids"])
    assert set(report["grounding_call_ids"]) < all_ids and len(all_ids) == 3

    suspect = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|Authorization:\s*Bearer\s+\S+)", re.I)
    suspect_files = []
    for row in manifest["files"]:
        path = RESULT / row["path"]
        if suspect.search(path.read_bytes()):
            suspect_files.append(row["path"])
    assert not suspect_files

    reference = plan["retained_v1_reference"]
    deltas = {
        "input_tokens": report["usage"]["input_tokens"] - reference["input_tokens"],
        "cached_input_tokens": report["usage"]["cached_input_tokens"] - reference["cached_input_tokens"],
        "output_tokens": report["usage"]["output_tokens"] - reference["output_tokens"],
        "reasoning_output_tokens": report["usage"]["reasoning_output_tokens"] - reference["reasoning_output_tokens"],
        "six_task_elapsed_ms": report["six_task_elapsed_ms"] - reference["six_task_elapsed_ms"],
        "whole_command_elapsed_ms": report["whole_command_elapsed_ms"] - reference["whole_command_elapsed_ms"],
        "input_feedback_median_ms": report["input_feedback_median_ms"] - reference["input_feedback_median_ms"],
    }
    audit = {
        "schema": "golden-desktop-app-server-v3-live-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_SINGLE_SUCCESS",
        "exact_tasks": 6,
        "routes": report["routes"],
        "preflight_model_calls": 1,
        "grounding_processes": 1,
        "grounding_threads": 1,
        "grounding_turns": 2,
        "unique_model_call_ids": 3,
        "mcp_startup_notifications": 0,
        "terminal_programs": 57,
        "verified_terminal_releases": 57,
        "old_target_pointer_admissions": 0,
        "repair_succeeded": True,
        "usage": report["usage"],
        "six_task_elapsed_ms": report["six_task_elapsed_ms"],
        "whole_command_elapsed_ms": report["whole_command_elapsed_ms"],
        "input_feedback_median_ms": report["input_feedback_median_ms"],
        "descriptive_delta_from_retained_v1": deltas,
        "credential_pattern_matches": 0,
        "comparison_limit": plan["comparison_limit"],
        "scope": plan["scope"],
    }
    (RESULT / "app-server-audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
