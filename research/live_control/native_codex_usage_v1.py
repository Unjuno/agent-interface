"""Accounting for the native Codex fields that the provider reports per call."""

try:
    from .integrated_efficiency_protocol_v1 import USAGE_FIELDS
except ImportError:
    from integrated_efficiency_protocol_v1 import USAGE_FIELDS


POLICY = "native-cache-write-optional-v1"
CACHE_WRITE = "cache_write_input_tokens"
REQUIRED_USAGE = set(USAGE_FIELDS) - {CACHE_WRITE}


def preflight_terminal(events):
    lifecycle = [row for row in events if row.get("type") in
                 ("thread.started", "turn.started", "turn.completed", "turn.failed", "error")]
    if ([row["type"] for row in lifecycle] != ["thread.started", "turn.started", "turn.completed"]
            or type(lifecycle[0].get("thread_id")) is not str or not lifecycle[0]["thread_id"]):
        raise ValueError("native preflight requires one started and successfully completed turn")
    return lifecycle[-1]


def normalize_usage(value):
    """Keep optional cache-write absent; validate each reported count."""
    if type(value) is not dict or not REQUIRED_USAGE <= value.keys():
        raise ValueError("native Codex usage is missing a required field")
    usage = {field: value[field] for field in USAGE_FIELDS if field in value}
    if any(type(amount) is not int or amount < 0 for amount in usage.values()):
        raise ValueError("native Codex usage contains an invalid count")
    if (usage["cached_input_tokens"] > usage["input_tokens"]
            or usage["reasoning_output_tokens"] > usage["output_tokens"]):
        raise ValueError("native Codex usage contains an invalid token subset")
    return usage


def accounting(calls):
    observed = [normalize_usage(call["usage"]) for call in calls]
    coverage = {field: sum(field in usage for usage in observed) for field in USAGE_FIELDS}
    totals = {field: (sum(usage[field] for usage in observed)
                     if coverage[field] == len(observed) else None)
              for field in USAGE_FIELDS}
    return {"usage": totals, "usage_coverage": coverage,
            "usage_status": "complete" if coverage[CACHE_WRITE] == len(observed) else "partial"}
