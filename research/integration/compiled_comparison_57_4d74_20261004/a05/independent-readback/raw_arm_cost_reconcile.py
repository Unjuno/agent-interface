"""Direct raw-row A05 per-arm accounting check; no producer execution."""
import collections
import json
import subprocess
from pathlib import Path

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
REF = "58bcbb4c45501880db8782158ddd3add3b765984"
BASE = "research/integration/compiled_comparison_57_4d74_20261004/a05/formal-output"
USAGE_FIELDS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens",
)


def read_json(path):
    raw = subprocess.check_output(["git", "-C", REPO, "show", f"{REF}:{BASE}/{path}"])
    return json.loads(raw)


def add_usage(target, usage):
    for field in USAGE_FIELDS:
        target[field] += (usage or {}).get(field, 0)


arms = {arm: {
    "tasks": 0, "exact": 0, "task_model_attempts": 0,
    "task_usage": dict.fromkeys(USAGE_FIELDS, 0),
    "task_elapsed_ns": 0,
    "preflight_attempts": 0,
    "preflight_usage": dict.fromkeys(USAGE_FIELDS, 0),
    "preflight_wait_ns": 0,
} for arm in "ABCD"}
all_task_calls = []
for block in (1, 2):
    for arm in "ABCD":
        bucket = arms[arm]
        evaluation = read_json(f"block-{block}/{arm}/independent-evaluation.json")
        assert evaluation["record_count"] == sum(evaluation["exact_counts"].values())
        bucket["exact"] += evaluation["record_count"]
        for task_index in range(1, 7):
            row = read_json(f"block-{block}/{arm}/task-{task_index}.json")
            assert row["task"]["task_id"] == f"task-{task_index}"
            bucket["tasks"] += 1
            bucket["task_elapsed_ns"] += row["elapsed_ns"]
            ledger = row["caller"].get("model_call_ledger", [])
            assert row["caller"].get("accounting", {}).get("attempted_calls", 0) == len(ledger)
            bucket["task_model_attempts"] += len(ledger)
            for call in ledger:
                add_usage(bucket["task_usage"], call.get("usage"))
                all_task_calls.append(call)

for arm in "ABC":
    bucket = arms[arm]
    for block in (1, 2):
        preflight = read_json(f"block-{block}/{arm}/schema-preflight.json")
        bucket["preflight_attempts"] += 1
        bucket["preflight_wait_ns"] += preflight["wait_ns"]
        add_usage(bucket["preflight_usage"], preflight.get("usage"))

raw_results = [read_json(f"model-calls/call-{i:03d}/result.json") for i in range(1, 27)]
assert len(raw_results) == read_json("HOST.json")["model_calls"] == 26
raw_usage = dict.fromkeys(USAGE_FIELDS, 0)
for result in raw_results:
    add_usage(raw_usage, result.get("usage"))

joined_usage = dict.fromkeys(USAGE_FIELDS, 0)
attempts = 0
for bucket in arms.values():
    attempts += bucket["task_model_attempts"] + bucket["preflight_attempts"]
    add_usage(joined_usage, bucket["task_usage"])
    add_usage(joined_usage, bucket["preflight_usage"])

assert attempts == len(raw_results) == 26
assert joined_usage == raw_usage, {"joined": joined_usage, "raw_results": raw_usage}
assert {arm: bucket["exact"] for arm, bucket in arms.items()} == {
    "A": 12, "B": 12, "C": 9, "D": 12,
}

for bucket in arms.values():
    bucket["all_attempt_input_plus_output"] = sum(
        bucket["task_usage"][field] + bucket["preflight_usage"][field]
        for field in ("input_tokens", "output_tokens")
    )
    bucket["task_plus_preflight_wait_seconds"] = (
        bucket["task_elapsed_ns"] + bucket["preflight_wait_ns"]
    ) / 1e9

report = {
    "source_revision": REF,
    "input_scope": "48 raw task JSONs, eight independent-evaluation JSONs, six raw preflight JSONs, 26 raw model-call results, HOST.json",
    "attempts": attempts,
    "raw_provider_usage": raw_usage,
    "joined_task_plus_preflight_usage": joined_usage,
    "raw_results_equal_joined_usage": raw_usage == joined_usage,
    "arms": arms,
    "comparisons": {
        "B_vs_A_all_attempt_input_output_reduction": 1 - arms["B"]["all_attempt_input_plus_output"] / arms["A"]["all_attempt_input_plus_output"],
        "B_vs_A_task_plus_preflight_wait_reduction": 1 - arms["B"]["task_plus_preflight_wait_seconds"] / arms["A"]["task_plus_preflight_wait_seconds"],
        "C_vs_B_all_attempt_input_output_change": arms["C"]["all_attempt_input_plus_output"] / arms["B"]["all_attempt_input_plus_output"] - 1,
        "C_vs_B_task_plus_preflight_wait_change": arms["C"]["task_plus_preflight_wait_seconds"] / arms["B"]["task_plus_preflight_wait_seconds"] - 1,
    },
    "limits": [
        "Retained-record arithmetic only; no original host, collateral-state, authority, or human setup verification.",
        "Cached input and reasoning output are subsets, not extra tokens.",
        "No task/model/provider/GUI/runner was executed.",
    ],
}
print(json.dumps(report, indent=2, sort_keys=True))
