"""Fail-closed v6 launcher and online-window evidence contracts.

This module is construction-only. It does not import the model runner and does
not allocate an optimizer or consume a formal seed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

ALLOCATION = "needle-role-skill-joint-retention-20260928-v6"
SEEDS = (9980211, 9980311, 9980411)
IMAGE_ID = "sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e"
ENTRYPOINT = "python"


def docker_argv(source: Path, output: Path) -> list[str]:
    """Return the complete intended Docker argv, with all paths realized."""
    try:
        source = source.resolve(strict=True)
        output = output.resolve(strict=True)
    except OSError as exc:
        raise ValueError("source and output must be existing directories") from exc
    if not source.is_dir() or not output.is_dir():
        raise ValueError("source and output must be existing directories")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("source_output_must_be_disjoint")
    return [
        "docker", "run", "--pull=never", "--platform=linux/amd64",
        "--network=none", "--read-only", "--cpus=1", "--memory=2g",
        "--pids-limit=64", "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m",
        "--entrypoint=python",
        "--mount", f"type=bind,source={source},target=/src,readonly",
        "--mount", f"type=bind,source={output},target=/out",
        "--workdir=/src", "--env=NEEDLE_OUTPUT=/out",
        "--env=NEEDLE_SEEDS=" + ",".join(map(str, SEEDS)),
        IMAGE_ID, "-B", "/src/runner.py",
    ]


def exact_argv_matches(realized: Any, expected: list[str]) -> bool:
    """No subset/semantic-equivalence acceptance: token count and order matter."""
    return isinstance(realized, list) and all(isinstance(token, str) for token in realized) and realized == expected


def _interval(row: Any, start: str, end: str) -> tuple[int, int] | None:
    if not isinstance(row, dict):
        return None
    left, right = row.get(start), row.get(end)
    if type(left) is not int or type(right) is not int or left < 0 or right <= left:
        return None
    return left, right


def online_window_errors(record: Any) -> list[str]:
    """Check retained event intervals for real arrival/update/query overlap.

    A valid feedback record must be newly arrived during a query window, be
    consumed before that same window closes, and have a non-empty optimizer
    interval that overlaps the query's inference interval. The auditor also
    requires worker identity to differ from inference identity; timestamps
    alone cannot prove concurrent execution.
    """
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["event_record_not_object"]
    queries = record.get("queries")
    feedback = record.get("feedback")
    if not isinstance(queries, list) or not queries:
        errors.append("queries_missing")
        queries = []
    if not isinstance(feedback, list) or not feedback:
        errors.append("feedback_missing")
        feedback = []

    query_by_id: dict[str, tuple[int, int, str, list[tuple[int, int]]]] = {}
    for index, query in enumerate(queries):
        interval = _interval(query, "inference_start_ns", "inference_end_ns")
        query_id = query.get("query_id") if isinstance(query, dict) else None
        worker = query.get("worker_id") if isinstance(query, dict) else None
        if not isinstance(query_id, str) or not query_id or interval is None or not isinstance(worker, str) or not worker:
            errors.append(f"query_invalid:{index}")
            continue
        if query_id in query_by_id:
            errors.append(f"query_duplicate:{query_id}")
            continue
        calls = query.get("inference_calls")
        valid_calls: list[tuple[int, int]] = []
        if not isinstance(calls, list) or not calls:
            errors.append(f"query_inference_calls_missing:{query_id}")
        else:
            for call_index, call in enumerate(calls):
                call_interval = _interval(call, "call_start_ns", "call_end_ns")
                if call_interval is None or not (interval[0] <= call_interval[0] < call_interval[1] <= interval[1]):
                    errors.append(f"inference_call_invalid:{query_id}:{call_index}")
                else:
                    valid_calls.append(call_interval)
        query_by_id[query_id] = (*interval, worker, valid_calls)

    seen_feedback: set[str] = set()
    overlap_count = 0
    for index, item in enumerate(feedback):
        if not isinstance(item, dict):
            errors.append(f"feedback_invalid:{index}")
            continue
        feedback_id = item.get("feedback_id")
        query_id = item.get("query_id")
        if not isinstance(feedback_id, str) or not feedback_id or feedback_id in seen_feedback:
            errors.append(f"feedback_id_invalid_or_duplicate:{index}")
            continue
        seen_feedback.add(feedback_id)
        arrival = item.get("arrived_ns")
        consumed = item.get("consumed_ns")
        update = _interval(item, "update_start_ns", "update_end_ns")
        trainer = item.get("trainer_worker_id")
        query = query_by_id.get(query_id)
        if type(arrival) is not int or type(consumed) is not int or arrival < 0 or consumed < arrival:
            errors.append(f"feedback_clock_invalid:{feedback_id}")
            continue
        if query is None:
            errors.append(f"feedback_query_missing:{feedback_id}")
            continue
        q_start, q_end, query_worker, calls = query
        if not (q_start < arrival <= consumed < q_end):
            errors.append(f"feedback_not_consumed_inside_query:{feedback_id}")
        if update is None or not (update[0] <= consumed <= update[1]):
            errors.append(f"update_interval_does_not_cover_consumption:{feedback_id}")
            continue
        if not isinstance(trainer, str) or not trainer or trainer == query_worker:
            errors.append(f"workers_not_independent:{feedback_id}")
        if any(max(update[0], call_start) < min(update[1], call_end)
               for call_start, call_end in calls):
            overlap_count += 1
        else:
            errors.append(f"update_does_not_overlap_inference_call:{feedback_id}")

    if overlap_count == 0:
        errors.append("no_verified_query_update_overlap")
    return errors
