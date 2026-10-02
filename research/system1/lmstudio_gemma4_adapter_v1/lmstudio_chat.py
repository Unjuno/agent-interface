"""Single-request, loopback-only LM Studio adapter for frozen image decisions."""

import base64
import json
import math
import time
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.parse import urlsplit


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _validate_inputs(endpoint_url, model, system_prompt, intent, image_bytes, schema, timeout_s):
    if not isinstance(endpoint_url, str):
        raise ValueError("endpoint must be the LM Studio chat-completions loopback URL")
    parsed = urlsplit(endpoint_url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.path != "/v1/chat/completions"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("endpoint must be the LM Studio chat-completions loopback URL")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("endpoint has an invalid port") from exc
    if port is None or not 1 <= port <= 65535:
        raise ValueError("endpoint must include a valid local port")
    for name, value in (
        ("model", model),
        ("system_prompt", system_prompt),
        ("intent", intent),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be non-empty text")
    if not isinstance(image_bytes, bytes) or not image_bytes:
        raise ValueError("image_bytes must be non-empty bytes")
    if not isinstance(schema, dict) or not schema:
        raise ValueError("schema must be a non-empty object")
    properties = schema.get("properties")
    required = schema.get("required")
    if (
        schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
        or not isinstance(properties, dict)
        or not properties
        or not all(isinstance(name, str) and name for name in properties)
        or not isinstance(required, list)
        or not all(isinstance(name, str) and name for name in required)
        or len(required) != len(set(required))
        or set(required) != set(properties)
    ):
        raise ValueError("schema must be a closed object with every property required")
    if (
        isinstance(timeout_s, bool)
        or not isinstance(timeout_s, (int, float))
        or not math.isfinite(timeout_s)
        or timeout_s <= 0
    ):
        raise ValueError("timeout_s must be a finite positive number")


def _counter(mapping, key):
    if key not in mapping:
        return None
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"LM Studio returned an invalid {key} counter")
    return value


def call_local(
    *, endpoint_url, model, system_prompt, intent, image_bytes, schema, timeout_s=180
):
    """Make exactly one local request; never retry or follow a redirect.

    The caller remains responsible for validating the parsed decision against
    the frozen decision contract and for retaining the returned raw response.
    """
    started_ns = time.perf_counter_ns()
    _validate_inputs(
        endpoint_url, model, system_prompt, intent, image_bytes, schema, timeout_s
    )
    schema_copy = json.loads(json.dumps(schema, allow_nan=False))
    data_url = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": intent},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "grounded_decision",
                "strict": True,
                "schema": schema_copy,
            },
        },
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 256,
        "stream": False,
    }
    request = Request(
        endpoint_url,
        data=json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    opener = build_opener(_NoRedirect)
    with opener.open(request, timeout=timeout_s) as response:
        raw_body = response.read()

    try:
        raw_response = json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("LM Studio response was not valid JSON") from exc
    if not isinstance(raw_response, dict):
        raise ValueError("LM Studio response must be a JSON object")

    choices = raw_response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise ValueError("LM Studio response must contain exactly one choice")
    choice = choices[0]
    if choice.get("finish_reason") != "stop":
        raise ValueError("LM Studio response did not finish normally")
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise ValueError("LM Studio response has no assistant message")
    content = message.get("content")
    if not isinstance(content, str) or not content:
        raise ValueError("LM Studio assistant content must be non-empty text")
    try:
        decision = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("LM Studio assistant content was not valid JSON") from exc
    if not isinstance(decision, dict):
        raise ValueError("LM Studio assistant JSON must be an object")

    raw_usage = raw_response.get("usage")
    if raw_usage is None:
        raw_usage = {}
    if not isinstance(raw_usage, dict):
        raise ValueError("LM Studio usage must be an object when present")
    prompt_details = raw_usage.get("prompt_tokens_details", {})
    completion_details = raw_usage.get("completion_tokens_details", {})
    if prompt_details is None:
        prompt_details = {}
    if completion_details is None:
        completion_details = {}
    if not isinstance(prompt_details, dict) or not isinstance(completion_details, dict):
        raise ValueError("LM Studio token detail fields must be objects")
    usage = {
        "input_tokens": _counter(raw_usage, "prompt_tokens"),
        "output_tokens": _counter(raw_usage, "completion_tokens"),
        "total_tokens": _counter(raw_usage, "total_tokens"),
        "cached_input_tokens": _counter(prompt_details, "cached_tokens"),
        "reasoning_output_tokens": _counter(completion_details, "reasoning_tokens"),
        "cost_usd": None,
    }
    actual_model = raw_response.get("model")
    if actual_model is not None and (not isinstance(actual_model, str) or not actual_model):
        raise ValueError("LM Studio response model must be non-empty text when present")
    latency_ns = time.perf_counter_ns() - started_ns
    return {
        "response_id": raw_response.get("id"),
        "requested_model": model,
        "actual_model": actual_model,
        "decision": decision,
        "latency_ns": latency_ns,
        "usage": usage,
        "raw_usage": raw_response.get("usage"),
        "raw_response": raw_response,
    }


__all__ = ["call_local"]
