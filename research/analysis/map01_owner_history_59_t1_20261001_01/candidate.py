"""One-shot offline candidate over a frozen synthetic workflow-run history."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research/orchestration/o3-g7/global-owner"))
from formal_allocation_global_owner_v1 import select_global_owner  # noqa: E402
from history_candidate import build_runs_url, collect_pages  # noqa: E402


def run_fixture(fixture: dict) -> dict:
    complete = collect_pages(
        fixture["pages"], max_pages=fixture["max_pages"], page_size=fixture["page_size"]
    )
    owner = select_global_owner(
        complete,
        current_run_id=fixture["current_run_id"],
        workflow_path=fixture["workflow_path"],
        allocation_id=fixture["allocation_id"],
        required_branch=fixture["required_branch"],
    )
    url = build_runs_url(
        "https://api.github.com",
        "Unjuno/agent-interface",
        Path(fixture["workflow_path"]).name,
        page=1,
    )
    return {
        "schema": "map01-owner-history-candidate-v1",
        "history": complete,
        "owner": owner,
        "first_page_url": url,
        "event_filter_present": "event=" in url,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run_fixture(json.loads(args.fixture.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result_class": result["owner"]["result_class"], "rows": len(result["history"]["workflow_runs"]), "event_filter_present": result["event_filter_present"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
