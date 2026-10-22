"""Adapt the current integrated-efficiency model-call boundary to the ledger.

The request is the exact wrapper input, and the response is the model runner's
JSONL event file. Neither is an upstream provider wire capture; hidden retries
and provider-side accounting require independent reconciliation.
"""

import asyncio
import base64
import hashlib
import json
import subprocess
from pathlib import Path


def _json_bytes(value):
    return json.dumps(value, allow_nan=False, separators=(",", ":"),
                      sort_keys=True).encode("utf-8")


def _usage(result):
    source = result.get("usage") if isinstance(result, dict) else None
    if not isinstance(source, dict):
        source = {}
    counts = {name: source.get(name) for name in
              ("input_tokens", "output_tokens")}
    for name, value in counts.items():
        if type(value) is not int or value < 0:
            counts[name] = None
    known = sum(value is not None for value in counts.values())
    return {"status": "reported" if known == 2 else
            "partial" if known else "unavailable", **counts}


def build_model_provider_call(*, model_call, root, prompt, image, contract,
                              workspace):
    """Return wrapper-input bytes and an async recorder-compatible callback.

    ``model_call`` has the current integrated model interface
    ``(root, prompt, image, contract, workspace)`` and is synchronous. It is
    run in a worker thread so the public MCP event loop remains available.
    """
    if not callable(model_call):
        raise TypeError("model_call must be callable")
    root = Path(root)
    image = Path(image)
    image_bytes = image.read_bytes()
    request_bytes = _json_bytes({
        "prompt": prompt,
        "contract": contract,
        "workspace": str(Path(workspace).resolve()),
        "image": {
            "path": image.name,
            "mime_type": "application/octet-stream",
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "data_base64": base64.b64encode(image_bytes).decode("ascii"),
        },
    })
    events_path = root / "model" / "events.jsonl"

    def event_bytes():
        try:
            return events_path.read_bytes()
        except OSError:
            return None

    async def provider_call():
        task = asyncio.create_task(asyncio.to_thread(
            model_call, root, prompt, image, contract, Path(workspace)))
        cancelled = False
        try:
            result = await asyncio.shield(task)
        except asyncio.CancelledError:
            # Keep custody until the synchronous call ends; to_thread cannot
            # terminate its worker. The actual model runner has its own bound.
            cancelled = True
            try:
                result = await task
            except BaseException as exc:
                result = None
                error = exc
            else:
                error = None
        except BaseException as exc:
            result = None
            error = exc
        else:
            error = None

        raw = event_bytes()
        if cancelled:
            return {"status": "cancelled", "usage": _usage(None),
                    "response_bytes": raw, "error_type": "CancelledError"}
        if error is not None:
            status = ("timeout" if isinstance(
                error, (TimeoutError, subprocess.TimeoutExpired)) else "failed")
            return {"status": status, "usage": _usage(None),
                    "response_bytes": raw,
                    "error_type": type(error).__name__}
        return {"status": "completed", "usage": _usage(result),
                "response_bytes": raw, "backend_result": result}

    return request_bytes, provider_call


def parse_agent_message(response_bytes):
    """Extract the sole completed agent message from captured JSONL events."""
    if not isinstance(response_bytes, bytes):
        raise TypeError("generation response must be raw JSONL bytes")
    events = [json.loads(line) for line in response_bytes.splitlines() if line]
    messages = [event["item"]["text"] for event in events
                if event.get("type") == "item.completed" and
                event.get("item", {}).get("type") == "agent_message"]
    if len(messages) != 1:
        raise ValueError("exactly one completed agent message is required")
    value = json.loads(messages[0])
    if not isinstance(value, dict):
        raise ValueError("agent message must encode a JSON object")
    return value
