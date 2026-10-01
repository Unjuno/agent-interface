from __future__ import annotations

import json
import time
from pathlib import Path

from runtime.cli_v1.api import dispatch


def main() -> None:
    meta = json.loads(Path("/tmp/observer.meta.json").read_text())
    started = time.monotonic_ns()
    program = {
        "schema": "agent-interface/program-v1",
        "program_id": "safety3066v3-construction",
        "source": {"observation_seq": 1, "binding_revision": 1},
        "authority": {
            "lease_id": "safety3066v3-construction-lease",
            "expires_at_ns": started + 1_000_000_000,
        },
        "terminal": {"release_all_required": True},
        "ops": [
            {"op": "focus", "target": "target"},
            {"op": "key_state", "key": "F8", "down": True},
            {"op": "wait_update", "timeout_ms": 30},
            {"op": "release_all"},
        ],
    }
    result = dispatch(
        program,
        {"target": meta["window_id"]},
        current_observation_seq=1, current_binding_revision=1,
        display_name=":199",
    )
    result = {
        "started_ns": started,
        "finished_ns": time.monotonic_ns(),
        "result": result,
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
