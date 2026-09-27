"""Audit the retained dependency failure before any app-server grounding turn."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULT = HERE / "results/golden-desktop-app-server-v2-live-01"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "golden_desktop_app_server_v2_live_v1_prereg.json")
    for path, expected in plan["source_sha256"].items():
        assert sha(ROOT / path) == expected, path
    manifest = read(RESULT / "retention-manifest.json")
    assert manifest["allocation_id"] == plan["allocation_id"]
    assert manifest["total_files"] == len(manifest["files"])
    assert manifest["total_bytes"] == sum(row["bytes"] for row in manifest["files"])
    for row in manifest["files"]:
        path = RESULT / row["path"]
        assert path.stat().st_size == row["bytes"] and sha(path) == row["sha256"], row["path"]
    failure = read(RESULT / "failure.json")
    assert failure == {
        "schema": "agent_interface_golden_failure_v1", "passed": False,
        "error_type": "StopIteration", "message": "",
        "output_retained": "results-local/golden-desktop-app-server-v2-live-01",
        "automatic_retry": False}
    gate = read(RESULT / "preflight/persistent/gate/gate-report.json")
    assert gate["accepted"] and gate["model_calls"] == gate["fresh_usage_records"] == 1
    protocol = [json.loads(line) for line in
                (RESULT / "persistent-grounding-app-server/protocol.jsonl").read_text().splitlines()]
    sent = [row["message"] for row in protocol if row["direction"] == "sent"]
    assert sum(row.get("method") == "thread/start" for row in sent) == 1
    assert sum(row.get("method") == "turn/start" for row in sent) == 0
    stderr = (RESULT / "arms/persistent/stderr.txt").read_text(encoding="utf-8")
    assert "ModuleNotFoundError: No module named 'openpyxl'" in stderr
    assert not (RESULT / "golden-report.json").exists()
    audit = {
        "schema": "golden-desktop-app-server-v2-failure-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "disposition": "RETAINED_PINNED_ENVIRONMENT_DEPENDENCY_FAILURE",
        "preflight_model_calls": 1,
        "grounding_threads_started": 1,
        "grounding_turns_started": 0,
        "gui_ready": False,
        "root_cause": "runtime/.venv and its doctor omit openpyxl although the GUI runtime imports it",
        "next_change": "add a pinned openpyxl dependency and make the next doctor import every runtime-required module before any model call",
        "limits": "dependency/harness evidence only; no app-server grounding, GUI task, correctness, latency or token comparison",
    }
    (RESULT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
