"""Generate the read-only A02 audit freeze after source files are final."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = [
    "SOURCE/A01/RAW.json", "SOURCE/A01/FREEZE.json", "SOURCE/A01/audit.py",
    "audit_a02.py", "test_a02.py", "build_freeze_a02.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    a01_freeze = json.loads((HERE / "SOURCE/A01/FREEZE.json").read_text(encoding="utf-8"))
    raw_hash = sha(HERE / "SOURCE/A01/RAW.json")
    freeze = {
        "schema": "map01_v39_cleanup_telemetry_bridge_a02_freeze_v1",
        "run_id": "MAP01-V39-CLEANUP-TELEMETRY-BRIDGE-A02-20261005",
        "predecessor": "A01 retained fake-display candidate; read-only audit successor",
        "a01_run_id": a01_freeze["run_id"],
        "a01_raw_sha256": raw_hash,
        "a01_freeze_sha256": sha(HERE / "SOURCE/A01/FREEZE.json"),
        "source_sha256": {p: sha(HERE / p) for p in SOURCES},
        "candidate_invocations": 0,
        "new_os_input": False,
        "new_gui_or_game": False,
        "new_model_call": False,
        "H": "An independent raw-only auditor can confirm A01's cancellation bracket and reject malformed sample/state/timing evidence.",
        "T": "Replay the exact retained A01 raw once through the A02 auditor; apply fourteen in-memory mutations; do not invoke the candidate.",
        "D": "PASS only when down/up brackets reconstruct and all fourteen malformed-evidence controls are rejected.",
        "C": "The retained candidate raw may be valid despite A01's weaker audit; A02 strengthens its audit only.",
        "U": "One key and one fake-display cancellation trace; no live OS input, GUI/game, application effect, useful feedback, recovery, or MAP01 progress.",
        "scope": "independent raw-only verification of A01 cleanup sample and operation brackets",
    }
    (HERE / "FREEZE-A02.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n",
                                          encoding="utf-8", newline="\n")
    print(json.dumps(freeze, sort_keys=True))


if __name__ == "__main__":
    main()
