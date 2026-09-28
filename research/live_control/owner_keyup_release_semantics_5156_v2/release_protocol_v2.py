"""Construction contract for separating explicit and autonomous owner releases.

This module does not drive X11. It validates a proposed, authority-neutral
receipt schema before any live owner instrumentation is attempted.
"""

AUTONOMOUS_REASONS = {
    "lease_expired", "cancelled", "focus_invalid", "owner_close", "owner_stop",
}
CALLER_FIELDS = {
    "caller_started_ns", "caller_returned_ns",
}
OWNER_FIELDS = {
    "owner_release_started_ns", "owner_sync_returned_ns",
}


class ProtocolError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProtocolError(message)


def _integer(value):
    return type(value) is int and value >= 0


def validate_receipt(row):
    """Validate one explicit-up or autonomous cleanup receipt.

    An explicit receipt must be nested in its exact synchronous caller call.
    An autonomous cleanup must carry no caller bracket at all; later client
    requests cannot be used to fabricate a bracket around it.
    """
    require(row.get("schema") == "owner-keyup-release-v2", "wrong receipt schema")
    require(row.get("grants_input_authority") is False, "authority flag must be false")
    require(isinstance(row.get("owner_id"), str) and row["owner_id"], "owner identity missing")
    require(isinstance(row.get("key"), str) and row["key"], "key identity missing")
    require(isinstance(row.get("intent_token"), str) and row["intent_token"],
            "intent identity missing")
    require(_integer(row.get("owner_sequence")) and row["owner_sequence"] > 0,
            "owner sequence invalid")
    require(row.get("owned_before") is True and row.get("owned_after") is False,
            "release receipt requires owned-to-empty transition")
    require(all(_integer(row.get(field)) for field in OWNER_FIELDS),
            "owner release bracket missing or invalid")
    owner_start = row["owner_release_started_ns"]
    owner_return = row["owner_sync_returned_ns"]
    require(owner_start <= owner_return, "owner timestamps inverted")

    kind = row.get("release_kind")
    if kind == "explicit_client_up":
        require(row.get("operation") in {"up", "button_up"}, "explicit operation invalid")
        require(isinstance(row.get("request_id"), str) and row["request_id"],
                "explicit request identity missing")
        require(all(_integer(row.get(field)) for field in CALLER_FIELDS),
                "explicit caller bracket missing or invalid")
        require(row["caller_started_ns"] <= owner_start <= owner_return
                <= row["caller_returned_ns"], "owner bracket escapes explicit caller")
        require(row.get("release_reason") is None, "explicit up has autonomous reason")
    elif kind == "autonomous_cleanup":
        require(row.get("operation") is None, "autonomous cleanup has client operation")
        require(row.get("request_id") is None, "autonomous cleanup has client request")
        require(row.get("release_reason") in AUTONOMOUS_REASONS,
                "autonomous reason missing or unknown")
        require(not (CALLER_FIELDS & row.keys()), "autonomous release has fabricated caller bracket")
    else:
        raise ProtocolError("unknown release kind")
    return row


def validate_stream(rows):
    """Validate identity uniqueness and owner-thread order for a receipt stream."""
    explicit_ids = set()
    owner_sequences = set()
    prev = {}
    checked = []
    for row in rows:
        validate_receipt(row)
        owner = row["owner_id"]
        seq = (owner, row["owner_sequence"])
        require(seq not in owner_sequences, "duplicate owner sequence")
        owner_sequences.add(seq)
        if row["release_kind"] == "explicit_client_up":
            identity = (owner, row["request_id"], row["key"])
            require(identity not in explicit_ids, "duplicate explicit release identity")
            explicit_ids.add(identity)
        if owner in prev:
            require(row["owner_sequence"] > prev[owner], "owner stream order is not increasing")
        prev[owner] = row["owner_sequence"]
        checked.append(row)
    return {
        "status": "PASS_RELEASE_EVENT_CLASSIFICATION_SCOPED",
        "receipt_count": len(checked),
        "explicit_receipts": sum(r["release_kind"] == "explicit_client_up" for r in checked),
        "autonomous_receipts": sum(r["release_kind"] == "autonomous_cleanup" for r in checked),
        "authority_grants": 0,
        "x11_observed": False,
    }
