"""Audit the frozen command-free app-server startup comparison."""
import hashlib
import json
import statistics
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/codex-app-server-startup-v1"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan = read(HERE / "codex_app_server_startup_v1_prereg.json")
    report = read(ROOT / "report.json")
    expected_order = [list(item) for item in plan["order"]]
    assert report["order"] == expected_order
    assert len(report["runs"]) == 6
    assert report["model_turns_started"] == report["model_calls"] == 0

    for path, expected in plan["source_sha256"].items():
        assert sha(REPO / path) == expected, path
    assert report["source_sha256"] == {
        Path(path).name: expected for path, expected in plan["source_sha256"].items()}

    protocol_turn_starts = 0
    observed = []
    for run in report["runs"]:
        assert [run["variant"], run["replicate"]] in expected_order
        assert run["thread_id_present"] and run["thread_ephemeral"] is True
        assert run["model_turns_started"] == run["model_calls"] == 0
        journal = ROOT / run["journal"]
        assert sha(journal) == run["journal_sha256"]
        rows = [json.loads(line) for line in journal.read_text().splitlines()]
        startup = [row for row in rows if row["direction"] == "received" and
                   row["message"].get("method") == "mcpServer/startupStatus/updated"]
        protocol_turn_starts += sum(
            row["direction"] == "sent" and row["message"].get("method") == "turn/start"
            for row in rows)
        assert len(startup) == run["mcp_startup_notifications"]
        assert sorted(set(row["message"]["params"]["name"] for row in startup)) == run["mcp_names"]
        observed.append((run["variant"], run["replicate"]))
    assert observed == [tuple(item) for item in expected_order]
    assert protocol_turn_starts == 0

    baseline = [run for run in report["runs"] if run["variant"] == "baseline"]
    minimal = [run for run in report["runs"] if run["variant"] == "minimal"]
    baseline_median = statistics.median(run["thread_start_ms"] for run in baseline)
    minimal_median = statistics.median(run["thread_start_ms"] for run in minimal)
    assert all(run["mcp_startup_notifications"] == 9 for run in baseline)
    assert all(run["mcp_startup_notifications"] == 0 for run in minimal)
    assert baseline_median == report["summary"]["baseline"]["thread_start_median_ms"]
    assert minimal_median == report["summary"]["minimal"]["thread_start_median_ms"]
    assert baseline_median - minimal_median == report["median_reduction_ms"]

    audit = {
        "schema": "codex-app-server-startup-audit-v1",
        "passed": True,
        "allocation_id": plan["allocation_id"],
        "runs": 6,
        "model_turns_started": 0,
        "model_calls": 0,
        "protocol_turn_start_messages": protocol_turn_starts,
        "baseline_thread_start_median_ms": baseline_median,
        "minimal_thread_start_median_ms": minimal_median,
        "median_reduction_ms": baseline_median - minimal_median,
        "baseline_startup_notifications": [run["mcp_startup_notifications"] for run in baseline],
        "minimal_startup_notifications": [run["mcp_startup_notifications"] for run in minimal],
        "decision": "use the capability-minimized command for a command-free persistent planner adapter",
        "limits": "same-host fresh-process thread creation only; three replicates per arm; no inference, task, token, controller-loop or cross-machine claim",
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
