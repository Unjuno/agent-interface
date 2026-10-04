"""Reconcile retained planner-contract r02 task and preflight accounting."""

from __future__ import annotations

import json
import subprocess


SOURCE_REVISION = "510c98fe46889461dce2a4c0e14e261eaa47e8ed"
PACKAGE = "research/integration/planner_contract_56_4d74_20261004/r02"
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
    name = row["arm"]
    arm = arms.setdefault(
        name,
        {
            "tasks": 0,
            "exact_submissions": 0,
            "graph_successes": 0,
            "graph_safe_yields": 0,
            "task_usage": dict.fromkeys(USAGE_FIELDS, 0),
            "task_elapsed_ns": 0,
            "task_model_wait_ns": 0,
            "task_models": 0,
            "preflight": {
                "count": 0,
                "usage": dict.fromkeys(USAGE_FIELDS, 0),
                "wait_ns": 0,
            },
        },
    )
    arm["tasks"] += row["saved_tasks"]
    arm["exact_submissions"] += row["independent"]["record_count"]
    arm["task_elapsed_ns"] += row["totals"]["task_elapsed_ns"]
    arm["task_model_wait_ns"] += row["totals"]["task_model_wait_ns"]
    arm["task_models"] += row["totals"]["task_models"]
    for task in row["tasks"]:
        arm["graph_successes"] += task.get("graph_outcome") == "TASK_SUCCEEDED"
        arm["graph_safe_yields"] += task.get("graph_outcome") == "SAFE_YIELD"
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

attempt_count = sum(
    arm["task_models"] + arm["preflight"]["count"] for arm in arms.values()
)
assert reconciled_usage == audit["all_attempt_usage"], (
    reconciled_usage,
    audit["all_attempt_usage"],
)
assert attempt_count == audit["host"]["model_calls"] == 29
assert {
    name: arm["exact_submissions"] for name, arm in arms.items()
} == {"A": 12, "B": 12, "C": 10, "D": 12}
assert (arms["C"]["graph_successes"], arms["C"]["graph_safe_yields"]) == (9, 3)

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
    "schema": "planner_contract_r02_per_arm_all_attempt_reconciliation_v1",
    "source_revision": SOURCE_REVISION,
    "experimental_source_snapshot": "13bab54ea6d91978247ecc1b70e5060db752367a",
    "source_paths": [
        f"{PACKAGE}/RETAINED_EVIDENCE_AUDIT.json",
        *[
            f"{PACKAGE}/formal-output/block-{block}/{name}/schema-preflight.json"
            for block in (1, 2)
            for name in ("A", "B", "C")
        ],
    ],
    "scope": (
        "read-only reconciliation of the separately frozen planner-contract r02 "
        "task rows and six arm/block schema preflights; no provider, GUI, or formal allocation"
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
        "C has 10/12 exact independent submissions but only 9/12 graph successes; it is not eligible for a benefit claim.",
        "D human setup cost is unavailable; task-scope elapsed is not full setup-to-effect latency.",
        "This is retained-JSON arithmetic, not original-host provenance, collateral-content, authority, or privacy verification.",
        "Do not pool this separately seeded allocation with compiled-comparison A05; it remains its own descriptive two-block result.",
    ],
}

print(json.dumps(report, indent=2, sort_keys=True))
