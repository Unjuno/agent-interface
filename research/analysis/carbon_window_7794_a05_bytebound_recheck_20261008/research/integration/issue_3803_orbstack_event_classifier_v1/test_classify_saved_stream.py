import json

import pytest

from classify_saved_stream import classify


SCHEMA = json.dumps({"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}).encode()


def stream(items, turns=1):
    rows = [{"type": "item.completed", "item": item} for item in items]
    rows += [{"type": "turn.completed", "usage": {"output_tokens": 1}} for _ in range(turns)]
    return ("\n".join(json.dumps(row) for row in rows) + "\n").encode()


def test_auxiliary_error_does_not_count_as_assistant():
    receipt, _ = classify(stream([{"type": "error"}, {"type": "agent_message", "text": '{"ok":true}'}]), SCHEMA)
    assert receipt["completed_assistant_message_count"] == 1
    assert receipt["completed_auxiliary_error_count"] == 1


@pytest.mark.parametrize("items", [
    [],
    [{"type": "agent_message", "text": '{"ok":true}'}, {"type": "agent_message", "text": '{"ok":true}'}],
    [{"type": "error"}],
    [{"type": "agent_message", "text": "not-json"}],
])
def test_ambiguous_or_malformed_assistant_refused(items):
    with pytest.raises((ValueError, json.JSONDecodeError)):
        classify(stream(items), SCHEMA)


def test_requires_single_completed_turn():
    with pytest.raises(ValueError, match="completed turn"):
        classify(stream([{"type": "agent_message", "text": '{"ok":true}'}], turns=2), SCHEMA)
