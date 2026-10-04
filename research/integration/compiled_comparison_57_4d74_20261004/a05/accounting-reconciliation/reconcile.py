"""Reconcile retained A05 task and schema-preflight usage without rerunning work."""

from __future__ import annotations

import json
import subprocess


SOURCE_REVISION = "58bcbb4c45501880db8782158ddd3add3b765984"
PACKAGE = "research/integration/compiled_comparison_57_4d74_20261004/a05"
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


def read_json_at_revision(path: str) -> dict:
    content = subprocess.check_output(
        ["git", "show", f"{SOURCE_REVISION}:{PACKAGE}/{path}"], text=True
    )
    return json.loads(content)


audit = read_json_at_revision("RETAINED_EVIDENCE_AUDIT.json")
arms: dict[str, dict] = {}

for row in audit["arms"]:
    arm = arms.setdefault(
        row["arm"],
        {
            "tasks": 0,
            "exact": 0,
            "task_usage": dict.fromkeys(USAGE_FIELDS, 0),
            "task_elapsed_ns": 0,
            "task_models": 0,
            "preflight": {
                "count": 0,
                "usage": dict.fromkeys(USAGE_FIELDS, 0),
                "wait_ns": 0,
            },
        },
    )
    arm["tasks"] += row["saved_tasks"]
    arm["exact"] += row["independent"]["record_count"]
    arm["task_elapsed_ns"] += row["totals"]["task_elapsed_ns"]
    arm["task_models"] += row["totals"]["task_models"]
    for field, value in row["totals"]["task_usage"].items():
        arm["task_usage"][field] += value

for name in ("A", "B", "C"):
    for block in (1, 2):
        preflight = read_json_at_revision(
            f"formal-output/block-{block}/{name}/schema-preflight.json"
        )
        totals = arms[name]["preflight"]
        totals["count"] += 1
        totals["wait_ns"] += preflight["wait_ns"]
        for field, value in preflight["usage"].items():
            totals["usage"][field] += value

reconciled_usage = dict.fromkeys(audit["all_attempt_usage"], 0)
for arm in arms.values():
    for field, value in arm["task_usage"].items():
        reconciled_usage[field] += value
    for field, value in arm["preflight"]["usage"].items():
        reconciled_usage[field] += value

assert reconciled_usage == audit["all_attempt_usage"], (
    reconciled_usage,
    audit["all_attempt_usage"],
)
attempt_count = sum(
    arm["task_models"] + arm["preflight"]["count"] for arm in arms.values()
)
assert attempt_count == audit["host"]["model_calls"] == 26
assert {name: arm["exact"] for name, arm in arms.items()} == {
    "A": 12,
    "B": 12,
    "C": 9,
    "D": 12,
}

for arm in arms.values():
    arm["attempt_count"] = arm["task_models"] + arm["preflight"]["count"]
    arm["all_attempt_input_plus_output"] = sum(
        arm["task_usage"][field] + arm["preflight"]["usage"][field]
        for field in ("input_tokens", "output_tokens")
    )
    arm["all_attempt_input_plus_output_per_planned_task"] = (
        arm["all_attempt_input_plus_output"] / arm["tasks"]
    )
    arm["task_input_plus_output"] = sum(
        arm["task_usage"][field] for field in ("input_tokens", "output_tokens")
    )
    arm["task_input_plus_output_per_planned_task"] = (
        arm["task_input_plus_output"] / arm["tasks"]
    )
    arm["task_elapsed_seconds"] = arm["task_elapsed_ns"] / 1e9
    arm["preflight_wait_seconds"] = arm["preflight"]["wait_ns"] / 1e9
    arm["task_plus_preflight_wait_seconds"] = (
        arm["task_elapsed_seconds"] + arm["preflight_wait_seconds"]
    )
    arm["task_plus_preflight_wait_seconds_per_planned_task"] = (
        arm["task_plus_preflight_wait_seconds"] / arm["tasks"]
    )

baseline, retained, rejected, _known_form = (arms[name] for name in "ABCD")
report = {
    "schema": "a05_per_arm_all_attempt_reconciliation_v1",
    "source_revision": SOURCE_REVISION,
    "source_paths": [
        f"{PACKAGE}/RETAINED_EVIDENCE_AUDIT.json",
        *[
            f"{PACKAGE}/formal-output/block-{block}/{name}/schema-preflight.json"
            for block in (1, 2)
            for name in ("A", "B", "C")
        ],
    ],
    "scope": (
        "read-only reconciliation of retained A05 task rows and six arm/block "
        "schema preflights; no provider, GUI, or formal allocation"
    ),
    "arms": arms,
    "reconciled_all_attempt_usage": reconciled_usage,
    "reconciled_model_attempts": attempt_count,
    "comparisons": {
        "B_vs_A_all_attempt_input_plus_output_reduction": 1
        - retained["all_attempt_input_plus_output"]
        / baseline["all_attempt_input_plus_output"],
        "B_vs_A_task_plus_preflight_wait_reduction": 1
        - retained["task_plus_preflight_wait_seconds"]
        / baseline["task_plus_preflight_wait_seconds"],
        "C_vs_B_all_attempt_input_plus_output_change": rejected[
            "all_attempt_input_plus_output"
        ]
        / retained["all_attempt_input_plus_output"]
        - 1,
        "C_vs_B_task_plus_preflight_wait_change": rejected[
            "task_plus_preflight_wait_seconds"
        ]
        / retained["task_plus_preflight_wait_seconds"]
        - 1,
    },
    "limits": [
        "Task plus preflight wait excludes process startup and final scoring time.",
        "Cached input and reasoning output are provider-reported subsets, not additive token totals.",
        "C fails exactness at 9/12 and is not eligible for a benefit claim.",
        "D human setup cost is unavailable; task-scope elapsed is not full setup-to-effect latency.",
        "This is retained-JSON arithmetic, not original-host provenance, collateral-content, authority, or privacy verification.",
    ],
}

print(json.dumps(report, indent=2, sort_keys=True))
