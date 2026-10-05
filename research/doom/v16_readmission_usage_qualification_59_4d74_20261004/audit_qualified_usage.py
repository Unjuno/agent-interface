"""Independent raw-input and provenance check for QUALIFIED_USAGE.json."""
import hashlib
import json
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
FREEZE = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
RUN = REPO / FREEZE["run_root"]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def find_response_usage(value):
    if isinstance(value, dict):
        names = {key.replace("_", "").lower()
                 for key in value if isinstance(key, str)}
        if names & {"tokenusagerecord", "turntokenusage", "responsetokenusage"}:
            return 1
        if any(isinstance(item, str) and item.replace("_", "").lower() ==
               "tokenusagerecord" for key, item in value.items()
               if key in {"type", "schema", "kind", "event"}):
            return 1
        return sum(find_response_usage(child) for child in value.values())
    if isinstance(value, list):
        return sum(find_response_usage(child) for child in value)
    return 0


def count_response_records():
    count = 0
    for path in [*RUN.rglob("*.json"), *RUN.rglob("*.jsonl")]:
        if path.name == "SAVED_READMISSION_AUDIT.json":
            continue
        try:
            values = jsonl(path) if path.suffix == ".jsonl" else [
                json.loads(path.read_text(encoding="utf-8"))]
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        count += sum(find_response_usage(value) for value in values)
    return count


def main():
    for path, expected in FREEZE["input_git_blobs"].items():
        actual = subprocess.check_output(
            ["git", "rev-parse", f"{FREEZE['source_commit']}:{path}"],
            cwd=REPO, text=True).strip()
        assert actual == expected, path
        assert sha256(REPO / path) == FREEZE["input_sha256"][path], path

    report_path = RUN / "episode/report.json"
    host_path = RUN / "host.stdout.jsonl"
    first_path = RUN / "SAVED_READMISSION_AUDIT.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    host_rows = jsonl(host_path)
    expected_threads = set(report["model_session_ids"])
    notifications = {}
    for row in host_rows:
        if row.get("method") != "thread/tokenUsage/updated":
            continue
        params = row["params"]
        if params.get("threadId") in expected_threads:
            notifications.setdefault(params["turnId"], []).append(params["tokenUsage"])

    statuses = []
    completed_last_sum = {"inputTokens": 0, "outputTokens": 0}
    interrupted_ids = []
    all_match = True
    previous_completed_snapshot = None
    repeated_interrupted_ids = []
    for decision in report["decisions"]:
        terminal = decision["final_action_admission"]["planner_terminal"]
        turn_id, status = terminal["turn_id"], terminal["status"]
        snapshots = notifications.get(turn_id, [])
        latest = snapshots[-1] if snapshots else None
        matches = latest is not None and decision.get("usage") == latest
        all_match &= matches
        statuses.append(status)
        if status == "completed" and latest is not None:
            completed_last_sum["inputTokens"] += latest["last"]["inputTokens"]
            completed_last_sum["outputTokens"] += latest["last"]["outputTokens"]
            previous_completed_snapshot = latest
        elif status == "interrupted":
            interrupted_ids.append(turn_id)
            if latest is not None and latest == previous_completed_snapshot:
                repeated_interrupted_ids.append(turn_id)

    first = json.loads(first_path.read_text(encoding="utf-8"))
    output_path = PACKAGE / "QUALIFIED_USAGE.json"
    qualified = json.loads(output_path.read_text(encoding="utf-8"))
    response_records = count_response_records()

    assert len(statuses) == 6 and statuses.count("completed") == 4
    assert statuses.count("interrupted") == 2
    assert len(notifications) == 6 and all_match
    assert completed_last_sum == {"inputTokens": 48773, "outputTokens": 1100}
    assert len(repeated_interrupted_ids) == 2
    assert response_records == 0
    assert first["known_completed_input"] == 71597
    assert first["known_completed_output"] == 1724
    assert qualified["completed_turn_last_snapshot_sum"] == completed_last_sum
    assert qualified["interrupted_turn_ids"] == interrupted_ids
    assert qualified["interrupted_incremental_usage"] == "UNKNOWN"
    assert qualified["response_level_usage_record_count"] == 0
    assert qualified["full_attempt_usage"] == "NOT_ESTABLISHED"
    assert qualified["preserved_first_audit"]["original_claimed_sum"] == {
        "input": 71597, "output": 1724}
    print(json.dumps({
        "status": "PASS_SNAPSHOT_RECONCILIATION; HOLD_FULL_USAGE_INTERPRETATION",
        "frozen_inputs": len(FREEZE["input_git_blobs"]),
        "turns": len(statuses),
        "completed_last_snapshot_sum": completed_last_sum,
        "interrupted_incremental_usage": "UNKNOWN",
        "repeated_interrupted_snapshots": len(repeated_interrupted_ids),
        "response_level_usage_records": response_records,
        "original_first_audit_preserved": True,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
