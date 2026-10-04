"""MAP01 v14: additive per-key release telemetry around session v12.

This measurement-only composition selects typed release backend v2, which
records program/step-bound admission and interval-censored ordinary key-up
receipts. The underlying session and controller policies remain unchanged.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent


def _option(name: str, default: str | None = None) -> str:
    args = sys.argv[1:]
    if name not in args:
        if default is not None:
            return default
        raise ValueError(f"required option missing: {name}")
    index = args.index(name)
    if index + 1 >= len(args):
        raise ValueError(f"option requires value: {name}")
    return args[index + 1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _merge_sources(out: Path) -> None:
    path = out / "sources.json"
    if not path.exists():
        return
    sources = json.loads(path.read_text(encoding="utf-8"))
    additions = (
        HERE / "session_map01_v14.py",
        HERE / "map01_overlap_controller_v40.py",
        HERE / "doom_typed_release_backend_v2.py",
        RESEARCH / "live_control/input_owner_v11.py",
    )
    for source in additions:
        sources[str(source.relative_to(RESEARCH)).replace("\\", "/")] = _sha(source)
    path.write_text(json.dumps(sources, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def main() -> None:
    out = Path(_option("--out"))
    import session_map01_v12 as base
    from doom_typed_release_backend_v2 import Backend as TelemetryBackend

    original_backend = base.Backend
    base.Backend = TelemetryBackend
    try:
        base.main()
    finally:
        base.Backend = original_backend
        _merge_sources(out)


if __name__ == "__main__":
    main()
