"""Action-scoped boundaries including provisional semantic probe feedback."""


FIELDS = {"accepted": "id", "input_released": "id", "terminal": "id",
          "observation": "id", "cancel_requested": "id", "semantic_probe": "id"}


def validate_scope(action_id, events):
    if action_id is None:
        return
    if not isinstance(action_id, str) or not 1 <= len(action_id) <= 128:
        raise ValueError("bounded action_id required")
    if any(event not in FIELDS for event in events):
        raise ValueError("unsupported scoped boundary event")


def boundary(record, events, action_id):
    name = record["event"]
    if action_id is None:
        return "boundary" if name in events else None
    if name not in events:
        return None
    identity = record.get(FIELDS[name])
    if not isinstance(identity, str) or not identity:
        return "identity_unknown"
    return "boundary" if identity == action_id else None
