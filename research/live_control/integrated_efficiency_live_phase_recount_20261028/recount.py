"""Recount saved #57 Chromium elapsed time by cold/warm/repair phase.

This reads the committed report only; it does not replay actors, model calls,
or the historical audit. The pinned report hash prevents silent input drift.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE_COMMIT = "52df8e2d934bd8b20d4d36da8a7f17a524c49210"
REPORT_PATH = "research/live_control/results/integrated-efficiency-live-01/report.json"
EXPECTED_REPORT_SHA256 = "84672ef551b97764c73ccdf4070b82db043d4e56bc509137e69c057c11aaa7da"
PHASES = {
    "cold_acquisition": ("task-1",),
    "warm_layout_a": ("task-2", "task-3"),
    "invalidation_repair": ("task-4",),
    "warm_after_repair": ("task-5", "task-6"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    report_bytes = subprocess.run(
        ["git", "show", f"{SOURCE_COMMIT}:{REPORT_PATH}"],
        cwd=ROOT, check=True, capture_output=True).stdout
    report_sha = hashlib.sha256(report_bytes).hexdigest()
    require(report_sha == EXPECTED_REPORT_SHA256, "pinned report SHA-256 mismatch")
    report = json.loads(report_bytes)
    arms = report["evaluation"]["arms"]
    preflight = report["preflight_calls"]
    expected_routes = {
        "plain": ["cold"] * 6,
        "persistent": ["cold", "reuse", "reuse", "repair", "reuse", "reuse"],
    }
    task_rows = {}
    for arm in ("plain", "persistent"):
        rows = arms[arm]["tasks"]
        require(len(rows) == 6, f"{arm}: expected six retained task rows")
        require([row["route"] for row in rows] == expected_routes[arm],
                f"{arm}: retained route sequence changed")
        require(all(row["exact_submission"] is True and row["releases_verified"] is True
                    for row in rows), f"{arm}: correctness or release gate failed")
        require([row["task_id"] for row in rows] == [f"task-{i}" for i in range(1, 7)],
                f"{arm}: task identity/order mismatch")
        task_rows[arm] = {row["task_id"]: row for row in rows}
        preflight_call = preflight[arm]
        preflight_tokens = preflight_call["usage"]["input_tokens"]
        task_tokens = sum(call["usage"]["input_tokens"]
                          for row in rows for call in row["model_calls"])
        require(preflight_tokens + task_tokens == arms[arm]["cumulative_input_tokens"][-1],
                f"{arm}: preflight + task input does not match cumulative report")
        require(sum(row["planner_generations"] for row in rows) + 1 ==
                arms[arm]["cumulative_planner_generations"][-1],
                f"{arm}: task generations + fresh preflight do not match cumulative report")

    phases = {}
    for phase, task_ids in PHASES.items():
        plain_ns = sum(task_rows["plain"][task]["elapsed_ns"] for task in task_ids)
        persistent_ns = sum(task_rows["persistent"][task]["elapsed_ns"] for task in task_ids)
        plain_input = sum(sum(call["usage"]["input_tokens"] for call in task_rows["plain"][task]["model_calls"])
                          for task in task_ids)
        persistent_input = sum(sum(call["usage"]["input_tokens"] for call in task_rows["persistent"][task]["model_calls"])
                              for task in task_ids)
        phases[phase] = {
            "task_ids": list(task_ids),
            "plain_elapsed_ns": plain_ns,
            "persistent_elapsed_ns": persistent_ns,
            "plain_minus_persistent_elapsed_ns": plain_ns - persistent_ns,
            "elapsed_reduction_fraction": (plain_ns - persistent_ns) / plain_ns,
            "plain_task_input_tokens_excluding_preflight": plain_input,
            "persistent_task_input_tokens_excluding_preflight": persistent_input,
        }

    result = {
        "schema": "integrated-efficiency-live-phase-recount-v1",
        "source_commit": SOURCE_COMMIT,
        "source_report_sha256": report_sha,
        "source_report": REPORT_PATH,
        "arms": {
            arm: {
                "task_elapsed_ns": [task_rows[arm][f"task-{i}"]["elapsed_ns"] for i in range(1, 7)],
                "reported_total_elapsed_ns": arms[arm]["elapsed_ns"],
                "cumulative_input_tokens_including_preflight": arms[arm]["cumulative_input_tokens"][-1],
                "preflight_input_tokens": preflight[arm]["usage"]["input_tokens"],
            }
            for arm in ("plain", "persistent")
        },
        "phase_comparison": phases,
        "interpretation": [
            "The reported elapsed advantage is concentrated in reuse phases, not cold acquisition or invalidation repair.",
            "The source is one fixed six-task sequence per arm; these are descriptive per-phase sums, not a population speed estimate.",
            "Input counts shown per phase exclude each arm's schema preflight; cumulative totals include the charged preflight.",
            "Cached input tokens remain a subset of input tokens and are not added to totals.",
            "This recount checks internal report arithmetic and gates; it does not independently re-audit raw model events or replay the experiment.",
        ],
    }
    (HERE / "recount.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(HERE / "recount.json")


if __name__ == "__main__":
    main()
