"""Typed no-authority outcomes for the controlled semantic grounding call."""
import json
from pathlib import Path

try:
    from . import semantic_repair_model_v1 as v1
except ImportError:
    import semantic_repair_model_v1 as v1


SCHEMA = "semantic-grounding-invocation-outcome-v1"
CAPACITY_MESSAGE = "Selected model is at capacity. Please try a different model."


def _events(output):
    path = Path(output) / "events.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def classify(output):
    """Classify one already-finished runner directory without retrying it."""
    output = Path(output)
    process_path = output / "process.json"
    if not process_path.is_file():
        raise ValueError("completed process record required")
    process = json.loads(process_path.read_text(encoding="utf-8"))
    events = _events(output)
    completed = [row for row in events if row.get("type") == "turn.completed"]
    messages = [row for row in events if row.get("type") == "item.completed"
                and row.get("item", {}).get("type") == "agent_message"]
    errors = [row.get("message", row.get("error", {}).get("message"))
              for row in events if row.get("type") in ("error", "turn.failed")]
    base = {"schema": SCHEMA, "requested_model": process.get("requested_model"),
            "requested_effort": process.get("requested_effort"),
            "process_exit_code": process.get("exit_code"),
            "model_threads_started": sum(row.get("type") == "thread.started" for row in events),
            "completed_turns": len(completed), "completed_messages": len(messages),
            "grants_semantic_authority": False, "grants_input_authority": False}
    if process.get("exit_code") == 0:
        try:
            result = v1.parse_output(output)
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            return {**base, "status": "FAILED_OUTPUT",
                    "reason": "invalid_model_output", "usage": None,
                    "result": None, "errors": [str(error)]}
        return {**base, "status": "COMPLETED", "reason": "validated_grounding",
                "usage": result["usage"], "result": result, "errors": []}
    if errors and all(message == CAPACITY_MESSAGE for message in errors):
        if completed or messages:
            raise ValueError("capacity deferral cannot contain completed output")
        return {**base, "status": "DEFERRED_UPSTREAM",
                "reason": "capacity_unavailable", "usage": None,
                "result": None, "errors": errors}
    return {**base, "status": "FAILED_UPSTREAM", "reason": "model_process_failed",
            "usage": None, "result": None, "errors": errors}


def invoke(output, prompt, image, workspace):
    """Run exactly once and return a typed outcome; this function never retries."""
    try:
        v1.call(output, prompt, image, workspace)
    except (RuntimeError, ValueError):
        pass
    return classify(output)
