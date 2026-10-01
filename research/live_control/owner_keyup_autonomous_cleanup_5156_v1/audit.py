"""Independent structural checks for captured owner-release JSONL."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED = {
    "event", "schema", "owner_id", "intent_token", "reason",
    "trigger_class", "key", "keycode", "request_started_ns",
    "request_returned_ns", "shared_sync_returned_ns",
    "grants_input_authority", "physical_key_up_claimed",
}


def audit(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    except Exception as exc:
        return [f"unreadable_jsonl:{type(exc).__name__}"]
    for index, row in enumerate(rows):
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"row_{index}:missing:{','.join(sorted(missing))}")
            continue
        if row["event"] != "owner_key_release_bracket" or row["schema"] != "owner-key-release-bracket-v1":
            errors.append(f"row_{index}:schema")
        if not all(isinstance(row[k], str) and row[k] for k in
                   ("owner_id", "reason", "trigger_class", "key")):
            errors.append(f"row_{index}:identity")
        times = [row[k] for k in ("request_started_ns", "request_returned_ns", "shared_sync_returned_ns")]
        if not all(type(t) is int for t in times) or times != sorted(times):
            errors.append(f"row_{index}:time_order")
        if row["grants_input_authority"] is not False or row["physical_key_up_claimed"] is not False:
            errors.append(f"row_{index}:overclaim")
        if type(row["keycode"]) is not int:
            errors.append(f"row_{index}:keycode")
    return errors


if __name__ == "__main__":
    import sys
    failures = audit(Path(sys.argv[1]))
    print(json.dumps({"ok": not failures, "errors": failures}, sort_keys=True))
    raise SystemExit(bool(failures))
