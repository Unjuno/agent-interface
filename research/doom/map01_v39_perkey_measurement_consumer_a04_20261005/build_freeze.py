from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = [
    "SOURCE/BRIDGE_RAW_A01.json", "SOURCE/BRIDGE_FREEZE_A01.json",
    "SOURCE/consumer_a03.py", "SOURCE/audit_a03.py", "SOURCE/FREEZE_A03.json",
    "candidate.py", "run_candidate.py", "audit.py", "test_a04.py", "build_freeze.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    a01_freeze_bytes = (HERE / "SOURCE/BRIDGE_FREEZE_A01.json").read_bytes()
    a03_freeze_bytes = (HERE / "SOURCE/FREEZE_A03.json").read_bytes()
    raw_bytes = (HERE / "SOURCE/BRIDGE_RAW_A01.json").read_bytes()
    freeze = {
        "schema": "map01_v39_perkey_measurement_consumer_a04_freeze_v1",
        "run_id": "MAP01-V39-PERKEY-MEASUREMENT-CONSUMER-A04-20261005",
        "H": "A retained V13 cancellation cleanup bracket can be projected into the strict A03 per-key consumer while preserving bridge admission context and actuation identity.",
        "T": "One offline projection of the exact retained #7774 A01 bridge raw; strict consumer plus independent raw-only A03 oracle; corruption controls only.",
        "D": "PASS only if one unique cleanup actuation joins to the contextualized down, the strict consumer and independent auditor agree, and every mutation is rejected.",
        "C": "This composes retained fake-display evidence after the fact; the projection was not emitted by A01's runtime bridge.",
        "U": "One key, one fake-display cancellation trace; no live OS input, GUI/game, model, application effect, useful feedback, recovery, or MAP01 progress.",
        "input_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "a01_freeze_sha256": hashlib.sha256(a01_freeze_bytes).hexdigest(),
        "a03_freeze_sha256": hashlib.sha256(a03_freeze_bytes).hexdigest(),
        "source_sha256": {name: sha(HERE / name) for name in SOURCES},
        "candidate_invocations_allowed": 1,
        "new_os_input": False, "new_gui_or_game": False, "new_model_call": False,
        "scope": "offline projection of retained fake-display cancellation cleanup into the strict per-key consumer contract",
    }
    (HERE / "FREEZE.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n",
                                       encoding="utf-8", newline="\n")
    print(json.dumps(freeze, sort_keys=True))


if __name__ == "__main__":
    main()
