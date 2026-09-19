#!/usr/bin/env python3
"""Exact provider-usage ledger separated from serialization proxies.

The semantic runtime never depends on this module. It exists at the planner/tool
boundary so a future codec experiment can compare exact provider usage only when
model, task set, environment and correctness are matched.
"""
from __future__ import annotations

from typing import Any

USAGE_FIELDS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens",
)
TOKEN_SOURCES = frozenset({"provider_usage", "proxy_only"})


class UsageError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise UsageError(message)


def validate_usage_record(record: dict[str, Any]) -> dict[str, Any]:
    _need(isinstance(record, dict), "usage record must be object")
    _need(record.get("schema") == "agent-interface/provider-usage-v0", "usage schema mismatch")
    _need(record.get("token_source") in TOKEN_SOURCES, "invalid token source")
    _need(isinstance(record.get("model"), str) and record["model"], "model required")
    for field in ("task_set_id", "environment_id", "source_commit", "source_path", "source_blob"):
        _need(isinstance(record.get(field), str) and record[field], f"{field} required")
    _need(type(record.get("successful_tasks")) is int and record["successful_tasks"] > 0,
          "successful_tasks must be positive int")
    _need(type(record.get("model_boundaries")) is int and record["model_boundaries"] >= 0,
          "model_boundaries must be nonnegative int")
    _need(type(record.get("model_visible_images")) is int and record["model_visible_images"] >= 0,
          "model_visible_images must be nonnegative int")
    usage = record.get("usage")
    _need(isinstance(usage, dict), "usage object required")
    for field in USAGE_FIELDS:
        value = usage.get(field)
        _need(type(value) is int and value >= 0, f"{field} must be nonnegative int")
    _need(type(record.get("correct")) is bool, "correct must be bool")
    if record["token_source"] == "proxy_only":
        _need(all(usage[field] == 0 for field in USAGE_FIELDS),
              "proxy-only record may not fabricate provider token counts")
    return record


def normalized_usage(record: dict[str, Any]) -> dict[str, float | int | str | bool]:
    validate_usage_record(record)
    tasks = record["successful_tasks"]
    return {
        "token_source": record["token_source"],
        "correct": record["correct"],
        "successful_tasks": tasks,
        "model_boundaries": record["model_boundaries"],
        "model_visible_images": record["model_visible_images"],
        "input_tokens_per_successful_task": record["usage"]["input_tokens"] / tasks,
        "output_tokens_per_successful_task": record["usage"]["output_tokens"] / tasks,
        "cached_input_tokens_per_successful_task": record["usage"]["cached_input_tokens"] / tasks,
    }


def comparison_eligible(left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, list[str]]:
    validate_usage_record(left)
    validate_usage_record(right)
    reasons: list[str] = []
    for field in ("model", "task_set_id", "environment_id"):
        if left[field] != right[field]:
            reasons.append(f"mismatch:{field}")
    if left["token_source"] != "provider_usage" or right["token_source"] != "provider_usage":
        reasons.append("exact_provider_usage_required")
    if not left["correct"] or not right["correct"]:
        reasons.append("equal_correctness_required")
    if left["successful_tasks"] != right["successful_tasks"]:
        reasons.append("mismatch:successful_tasks")
    return not reasons, reasons
