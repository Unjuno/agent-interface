"""Replay live-04's event-filtered run lookup against a cross-event fixture."""
from __future__ import annotations

import argparse
import json
import subprocess
import types
from pathlib import Path


def git_show(repo_root: Path, commit: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), "show", f"{commit}:{path}"], text=True
    )


def load_helper(repo_root: Path, fixture: dict):
    module = types.ModuleType("frozen_global_owner")
    source = git_show(repo_root, fixture["source_commit"], fixture["owner_helper_path"])
    exec(compile(source, fixture["owner_helper_path"], "exec"), module.__dict__)
    return module


def run(repo_root: Path, fixture: dict) -> dict:
    workflow = git_show(repo_root, fixture["source_commit"], fixture["workflow_path"])
    query = "runs?event=$GITHUB_EVENT_NAME&per_page=100"
    if query not in workflow or "workflow_dispatch:" not in workflow:
        raise ValueError("frozen live-04 workflow no longer has the preregistered trigger/query composition")

    helper = load_helper(repo_root, fixture)
    rows = fixture["runs"]
    results = []
    for current in rows:
        # Exact behavioral effect of the workflow's `event=$GITHUB_EVENT_NAME`
        # parameter: each event sees only rows with the current run's event.
        visible = [row for row in rows if row["event"] == current["event"]]
        payload = {
            "total_count": len(visible),
            "workflow_runs": visible,
        }
        result = helper.select_global_owner(
            payload,
            current_run_id=current["id"],
            workflow_path=fixture["workflow_path"],
            allocation_id=fixture["allocation_id"],
            required_branch=fixture["required_branch"],
        )
        results.append(
            {
                "current_run_id": current["id"],
                "event": current["event"],
                "api_visible_run_ids": [row["id"] for row in visible],
                "helper_result_class": result["result_class"],
                "may_enter_formal_step": result["may_enter_formal_step"],
                "helper_matching_run_count": result["matching_run_count"],
            }
        )
    return {
        "schema": "map01-cross-event-owner-candidate-v1",
        "source_commit": fixture["source_commit"],
        "workflow_path": fixture["workflow_path"],
        "allocation_id": fixture["allocation_id"],
        "query_event_filter": query,
        "workflow_has_push_and_dispatch": True,
        "rows": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("fixture.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    result = run(args.repo_root, fixture)
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
    args.out.write_text(serialized, encoding="utf-8", newline="\n")
    print(serialized, end="")


if __name__ == "__main__":
    main()
