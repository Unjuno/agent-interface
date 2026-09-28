"""Synthetic v3 receipt contract; validates metadata only, never drives X11."""

AUTONOMOUS_REASONS = {
    "stop_requested", "expired", "surface_changed", "focus_changed",
    "cancelled", "thread_exit",
}
OWNER_FIELDS = {"owner_release_started_ns", "owner_sync_returned_ns"}
CALLER_FIELDS = {"caller_started_ns", "caller_returned_ns"}
COMMON_FIELDS = {
    "schema", "grants_input_authority", "owner_id", "intent_token",
    "owner_sequence", "owned_before", "owned_after", *OWNER_FIELDS,
    "release_kind", "operation", "request_id", "release_reason",
}
EXPLICIT_FIELDS = {"caller_started_ns", "caller_returned_ns"}


class ProtocolError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProtocolError(message)


def _nat(value):
    return type(value) is int and value >= 0


def validate_receipt(row):
    require(type(row) is dict, "receipt must be an object")
    require(row.get("schema") == "owner-keyup-release-v3", "wrong schema")
    require(set(row) <= COMMON_FIELDS | EXPLICIT_FIELDS, "unknown field")
    require(row.get("grants_input_authority") is False, "authority must be false")
    require(type(row.get("owner_id")) is str and bool(row["owner_id"]), "owner missing")
    require(type(row.get("intent_token")) is str and bool(row["intent_token"]), "intent missing")
    require(_nat(row.get("owner_sequence")) and row["owner_sequence"] > 0, "sequence invalid")
    require(row.get("owned_before") is True and row.get("owned_after") is False,
            "release must transition owned to empty")
    require(all(_nat(row.get(k)) for k in OWNER_FIELDS), "owner bracket invalid")
    require(row["owner_release_started_ns"] <= row["owner_sync_returned_ns"],
            "owner timestamps inverted")

    if row.get("release_kind") == "explicit_client_up":
        op = row.get("operation")
        require(op in {"key_up", "button_up"}, "explicit operation invalid")
        require(type(row.get("request_id")) is str and bool(row["request_id"]),
                "explicit request missing")
        require(row.get("release_reason") is None, "explicit row has autonomous reason")
        require(all(_nat(row.get(k)) for k in CALLER_FIELDS), "caller bracket invalid")
        require(row["caller_started_ns"] <= row["owner_release_started_ns"]
                <= row["owner_sync_returned_ns"] <= row["caller_returned_ns"],
                "owner bracket escapes caller")
        if op == "key_up":
            require(type(row.get("key")) is str and bool(row["key"]), "key identity missing")
            require("button" not in row, "key_up has button identity")
        else:
            require("button" in row and type(row["button"]) is int
                    and row["button"] in (1, 2, 3), "button_up identity invalid")
            require("key" not in row, "button_up has key identity")
    elif row.get("release_kind") == "autonomous_cleanup":
        require(type(row.get("key")) is str and bool(row["key"]), "synthetic key identity missing")
        require(row.get("operation") is None and row.get("request_id") is None,
                "autonomous row has explicit identity")
        require(row.get("release_reason") in AUTONOMOUS_REASONS, "autonomous reason invalid")
        require(not (CALLER_FIELDS & row.keys()), "autonomous row has caller bracket")
        require("button" not in row, "autonomous synthetic row has button field")
    else:
        raise ProtocolError("unknown release kind")
    return row


def validate_stream(rows):
    seen = set()
    previous = {}
    for row in rows:
        validate_receipt(row)
        owner, seq = row["owner_id"], row["owner_sequence"]
        require((owner, seq) not in seen, "duplicate owner sequence")
        require(owner not in previous or seq > previous[owner], "owner sequence not increasing")
        seen.add((owner, seq))
        previous[owner] = seq
    return {"status": "PASS_SYNTHETIC_SCHEMA_COMPATIBILITY_ONLY",
            "receipt_count": len(rows), "authority_grants": 0, "x11_observed": False}

