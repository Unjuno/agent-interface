"""Nonformal Docker comparison: add a fixed wait after Ctrl-S in remap rows."""
from __future__ import annotations

import json
from pathlib import Path

from diagnose_remap import ROWS, run_row as run_remap_row


def run_row_with_wait(row: str, initial: str, target: str | None) -> dict:
    # Use the same fixture/backend/actor lifecycle, but a dedicated adapter below
    # augments the operation sequence before dispatch; no formal runner is used.
    return run_remap_row(row, initial, target, post_save_wait_ms=250)


if __name__ == "__main__":
    baseline = [run_remap_row(*spec, post_save_wait_ms=0) for spec in ROWS]
    waited = [run_row_with_wait(*spec) for spec in ROWS]
    result = {
        "scope": "nonformal Docker comparison; no formal allocation or Arch claim",
        "baseline": baseline,
        "post_save_wait_250ms": waited,
    }
    output = Path(__file__).with_name("results") / "diagnostic04" / "raw.json"
    output.parent.mkdir(parents=True, exist_ok=False)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result_path": str(output), "baseline": [
        {key: row[key] for key in ("row", "dispatch_status", "saved_effect", "actor_exit")}
        for row in baseline
    ], "waited": [
        {key: row[key] for key in ("row", "dispatch_status", "saved_effect", "actor_exit")}
        for row in waited
    ]}, sort_keys=True))
