"""Allocation 04 adapter around the frozen parent's supported main entrypoint."""
import json
from pathlib import Path
import uuid

import runner_effect_v2 as parent


MARKER = "agent-mcp-effect-2907-20260927-04"
parent.MARKER = MARKER
parent.base.MARKER = MARKER
OUT = parent.OUT


def annotate_trace(trace, transport_token):
    reads = trace.get("retained_reads", [])
    for row in reads:
        row["session_id"] = trace.get("session_id")
    if reads:
        trace["retained_transport"] = {
            "scope": "single-public-stdio-client-session",
            "session_id": trace.get("session_id"),
            "transport_token": transport_token,
            "read_count": len(reads),
            "same_client_context": True,
        }
    return trace


def persist_effect_from_xprop(command, result):
    if not isinstance(command, (list, tuple)) or "WM_NAME" not in command or "-id" not in command:
        return
    title = getattr(result, "stdout", "") or ""
    if MARKER not in title:
        return
    window_id = command[command.index("-id") + 1]
    receipt = {"window_id": window_id, "wm_name": title.strip(),
               "marker": MARKER, "matched": True}
    raw = json.dumps(receipt, sort_keys=True, indent=2).encode() + b"\n"
    (OUT / "effect_receipt.json").write_bytes(raw)


def main():
    token = uuid.uuid4().hex
    retained = parent.base.retained
    original_write_json = retained.write_json
    original_subprocess_run = parent.base.subprocess.run

    def write_json(path, value):
        if Path(path).name == "trace.json":
            annotate_trace(value, token)
        return original_write_json(path, value)

    def subprocess_run(command, *args, **kwargs):
        result = original_subprocess_run(command, *args, **kwargs)
        persist_effect_from_xprop(command, result)
        return result

    retained.write_json = write_json
    parent.base.subprocess.run = subprocess_run
    try:
        return parent.main()
    finally:
        retained.write_json = original_write_json
        parent.base.subprocess.run = original_subprocess_run


if __name__ == "__main__":
    raise SystemExit(main())

