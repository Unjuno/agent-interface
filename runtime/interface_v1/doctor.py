"""Unified, side-effect-free Agent Interface doctor."""
from __future__ import annotations

import json
from typing import Any, Mapping

from runtime.core_v1.contract import SCHEMA_BACKEND, SCHEMA_PROGRAM
from .native_probe import probe_native


def report(*, system: str | None = None, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    native = probe_native(system=system, env=env)
    return {
        "schema": "agent-interface/interface-doctor-v1",
        "core_contract": {"backend": SCHEMA_BACKEND, "program": SCHEMA_PROGRAM},
        "native_probe": native,
        "candidate_backend": native["candidate_backend"],
        "support_claim": False,
        "ready_for_side_effects": False,
        "reason": "Native API/permission evidence is discovery only; backend support requires a separate effect integration gate.",
    }


def main() -> int:
    print(json.dumps(report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
