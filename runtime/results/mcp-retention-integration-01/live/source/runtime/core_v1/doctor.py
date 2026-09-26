"""Print platform-neutral runtime-core diagnostics as JSON."""
from __future__ import annotations

import json
from .contract import SCHEMA_BACKEND, SCHEMA_PROGRAM
from .platform_probe import probe_platform


def report() -> dict[str, object]:
    probe = probe_platform()
    return {
        "schema": "agent-interface/runtime-core-doctor-v1",
        "contract": {"backend": SCHEMA_BACKEND, "program": SCHEMA_PROGRAM},
        "platform": probe,
        "native_backend_loaded": False,
        "ready_for_side_effects": False,
        "reason": "This lane promotes the semantic/backend contract only; native backend loading is separate.",
    }


def main() -> int:
    print(json.dumps(report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
