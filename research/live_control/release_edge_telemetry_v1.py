"""Pure helpers for bounded X11 release-edge telemetry.

The existing InputOwner v10 performs XTest KeyRelease followed by ``d.sync()``
before ``InputOwner.call('up', ...)`` returns.  A caller-side return timestamp is
therefore a conservative *post-sync* upper edge, not the exact internal sync
instant.  These helpers preserve that distinction and keep X11 state sampling
separate from release calls so a multi-key chord is not staggered by telemetry.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any


def time_release_call(
    key: str,
    release_call: Callable[[], Any],
    clock_ns: Callable[[], int],
) -> dict:
    """Time one existing release call without adding work inside the call.

    ``post_sync_call_return_ns`` is after the InputOwner worker's X11 ``d.sync``
    because the synchronous call cannot return before the worker completes.  It
    may be later than the actual sync instant because of queue/event scheduling.
    """
    if not isinstance(key, str) or not key:
        raise ValueError("nonempty key required")
    requested_ns = clock_ns()
    if type(requested_ns) is not int:
        raise TypeError("clock_ns must return int")
    release_call()
    returned_ns = clock_ns()
    if type(returned_ns) is not int:
        raise TypeError("clock_ns must return int")
    if returned_ns < requested_ns:
        raise AssertionError("monotonic clock moved backwards")
    return {
        "key": key,
        "release_call_requested_ns": requested_ns,
        "post_sync_call_return_ns": returned_ns,
        "call_bracket_ns": returned_ns - requested_ns,
    }


def keys_down_from_bitmap(bitmap: Sequence[int], keycodes: Mapping[str, int]) -> list[str]:
    """Decode selected X11 key states from a 256-bit query_keymap bitmap."""
    if len(bitmap) < 32:
        raise ValueError("X11 keymap bitmap must contain at least 32 bytes")
    result = []
    for key, code in keycodes.items():
        if not isinstance(key, str) or not key:
            raise ValueError("nonempty key name required")
        if type(code) is not int or not 0 <= code < 256:
            raise ValueError(f"invalid X11 keycode for {key!r}: {code!r}")
        if bitmap[code // 8] & (1 << (code % 8)):
            result.append(key)
    return sorted(result)


def finalize_release_batch(
    releases: Sequence[dict],
    sample_bitmap: Callable[[], Sequence[int]],
    keycodes: Mapping[str, int],
    clock_ns: Callable[[], int],
) -> dict:
    """Sample X11 key state once after a complete release batch.

    This helper deliberately does not call ``sample_bitmap`` between individual
    key releases.  The one sample occurs only after the caller has completed all
    release calls in the batch.
    """
    if not releases:
        raise ValueError("nonempty release batch required")
    released_keys = []
    previous_return = None
    for row in releases:
        key = row.get("key")
        requested = row.get("release_call_requested_ns")
        returned = row.get("post_sync_call_return_ns")
        if not isinstance(key, str) or not key:
            raise ValueError("release row missing key")
        if type(requested) is not int or type(returned) is not int or returned < requested:
            raise ValueError("invalid release call clocks")
        if previous_return is not None and requested < previous_return:
            raise ValueError("release rows are not sequential")
        previous_return = returned
        released_keys.append(key)
    if len(set(released_keys)) != len(released_keys):
        raise ValueError("duplicate key in release batch")

    sample_started_ns = clock_ns()
    if type(sample_started_ns) is not int:
        raise TypeError("clock_ns must return int")
    bitmap = sample_bitmap()
    sample_finished_ns = clock_ns()
    if type(sample_finished_ns) is not int:
        raise TypeError("clock_ns must return int")
    if sample_finished_ns < sample_started_ns:
        raise AssertionError("monotonic clock moved backwards during X11 sample")
    if previous_return is not None and sample_started_ns < previous_return:
        raise AssertionError("X11 state sample began before release calls returned")

    selected = {key: keycodes[key] for key in released_keys}
    still_down = keys_down_from_bitmap(bitmap, selected)
    return {
        "releases": [dict(row) for row in releases],
        "release_batch_first_requested_ns": releases[0]["release_call_requested_ns"],
        "release_batch_last_post_sync_return_ns": releases[-1]["post_sync_call_return_ns"],
        "x11_sample_started_ns": sample_started_ns,
        "x11_sample_finished_ns": sample_finished_ns,
        "x11_keys_down_after_release": still_down,
        "x11_all_released_after_batch": not still_down,
        "meaning": (
            "caller-side release brackets plus one post-release X11 keymap sample; "
            "not the exact internal d.sync timestamp and not hardware key state"
        ),
    }
