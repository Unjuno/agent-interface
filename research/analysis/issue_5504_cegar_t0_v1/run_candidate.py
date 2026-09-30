"""One-shot formal candidate runner. Refuses existing output and source drift."""

import hashlib
import json
import os
import platform
from pathlib import Path

from experiment import build_result, frozen_cases
from oracle import independent_oracle


ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.environ.get("AI5504_RESULTS_DIR", ROOT / "results" / "t0")) / "candidate.json"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def verify_frozen_sources():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    for name, expected in freeze["source_sha256"].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"STOP_SOURCE_HASH_MISMATCH:{name}")
    return freeze


def main():
    if OUTPUT.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    freeze = verify_frozen_sources()
    result = build_result(frozen_cases(), independent_oracle)
    envelope = {
        "allocation": freeze["allocation"],
        "image_digest": freeze["image_digest"],
        "python": platform.python_version(),
        "candidate": result,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical(envelope) + "\n")
    print(json.dumps({"decision": "CANDIDATE_WRITTEN", "path": str(OUTPUT), "sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
