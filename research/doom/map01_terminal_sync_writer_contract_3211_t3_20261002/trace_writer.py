from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


def write_jsonl(path: Path, events: Iterable[dict]) -> None:
    """Write one compact JSON object and one physical LF per event."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for event in events:
            stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")))
            stream.write("\n")


def write_legacy_control(path: Path, events: Iterable[dict]) -> None:
    """Reproduce the frozen runner's literal backslash+n delimiter as a control."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        for event in events:
            stream.write(json.dumps(event, sort_keys=True))
            stream.write("\\n")
