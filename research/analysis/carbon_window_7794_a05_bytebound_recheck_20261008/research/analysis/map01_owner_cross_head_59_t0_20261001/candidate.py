"""Replay frozen main's launch-owner helper over the retained duplicate-run IDs."""
import argparse
import json
import subprocess
import types
from pathlib import Path


def run(repo_root: Path, fixture: dict) -> dict:
    source = subprocess.check_output(
        ["git", "-C", str(repo_root), "show",
         fixture["source_commit"] + ":" + fixture["owner_helper_path"]],
        text=True,
    )
    helper = types.ModuleType("frozen_owner_helper")
    exec(compile(source, "<frozen-owner-helper>", "exec"), helper.__dict__)
    rows = []
    all_runs = [dict(row, path=fixture["workflow_path"]) for row in fixture["runs"]]
    for current in fixture["runs"]:
        rows.append(helper.select_owner(
            {"workflow_runs": all_runs},
            current_run_id=current["id"],
            workflow_path=fixture["workflow_path"],
            head_sha=current["head_sha"],
            allocation_id=fixture["allocation_id"],
        ))
    return {"schema": "map01-owner-cross-head-candidate-v1", "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("fixture.json"))
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    print(json.dumps(run(args.repo_root, fixture), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
