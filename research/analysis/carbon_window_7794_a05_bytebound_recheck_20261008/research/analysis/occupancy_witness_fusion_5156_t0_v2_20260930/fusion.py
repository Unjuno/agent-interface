"""Synthetic, proposal-only interval fusion for #5156/#4345 evidence."""

IDENTITY_FIELDS = ("owner_id", "actuation_id", "keycode", "display_id", "clock_id")


def _plain_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_interval(value):
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(_plain_int(x) for x in value)
        and value[0] <= value[1]
    )


def _valid_identity(identity):
    return (
        isinstance(identity, dict)
        and isinstance(identity.get("owner_id"), str)
        and bool(identity["owner_id"])
        and isinstance(identity.get("actuation_id"), str)
        and bool(identity["actuation_id"])
        and _plain_int(identity.get("keycode"))
        and isinstance(identity.get("display_id"), str)
        and bool(identity["display_id"])
        and isinstance(identity.get("clock_id"), str)
        and bool(identity["clock_id"])
    )


def fuse(record):
    """Return the conservative feasible key-up bracket; never grants authority."""
    unknown = {"decision": "UNKNOWN", "reason": "INVALID_EVIDENCE", "authority": False}
    if not isinstance(record, dict):
        return unknown
    down = record.get("down_query")
    up = record.get("up_query")
    release = record.get("owner_release")
    if not all(isinstance(item, dict) for item in (down, up, release)):
        return unknown
    sources = (down, up, release)
    identity = record.get("identity")
    if not _valid_identity(identity):
        return unknown
    if any(
        not _valid_identity(source)
        or any(source.get(field) != identity[field] for field in IDENTITY_FIELDS)
        for source in sources
    ):
        return {"decision": "UNKNOWN", "reason": "IDENTITY_MISMATCH", "authority": False}
    if not _valid_interval(down.get("query")) or not _valid_interval(up.get("query")):
        return unknown
    owner_start = release.get("request_start")
    request_return = release.get("request_return")
    sync_return = release.get("sync_return")
    if not all(_plain_int(x) for x in (owner_start, request_return, sync_return)):
        return unknown
    if not owner_start <= request_return <= sync_return:
        return {"decision": "UNKNOWN", "reason": "INVALID_OWNER_ORDER", "authority": False}
    release_count = release.get("release_count")
    repress_count = release.get("repress_count")
    if not _plain_int(release_count) or not _plain_int(repress_count):
        return unknown
    if release_count != 1 or repress_count != 0:
        return {"decision": "UNKNOWN", "reason": "NON_SINGLE_TRANSITION", "authority": False}

    # A DOWN snapshot somewhere in [d0,d1] implies release > d0; an UP
    # snapshot somewhere in [u0,u1] implies release <= u1. The owner bracket
    # independently gives release > request_start and <= sync_return.
    lower_open = max(down["query"][0], owner_start)
    upper_closed = min(up["query"][1], sync_return)
    if lower_open >= upper_closed:
        return {"decision": "UNKNOWN", "reason": "EMPTY_INTERSECTION", "authority": False}
    return {
        "decision": "BOUNDED",
        "lower_open": lower_open,
        "upper_closed": upper_closed,
        "authority": False,
    }
