"""Deterministically build one host-only synthetic cleanup trace."""

from __future__ import annotations

import json
from pathlib import Path

from release_envelope import record_release_envelopes


def build(path: Path) -> list[dict]:
    tick = iter((100, 110, 120, 130, 140))
    records = record_release_envelopes(
        display=object(),
        owned_keys=(("a", 38), ("b", 56)),
        owner_id="synthetic-owner",
        intent_token="synthetic-intent",
        reason="cancelled",
        trigger_class="owner_loop_cancel",
        key_release=lambda _display, _code: None,
        sync=lambda _display: None,
        clock_ns=lambda: next(tick),
    )
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in records), encoding="utf-8")
    return records


if __name__ == "__main__":
    import sys
    rows = build(Path(sys.argv[1]))
    print(json.dumps({"records": len(rows), "kind": "synthetic_host_only"}, sort_keys=True))
