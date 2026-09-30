"""Independent one-shot raw-only audit runner."""

import hashlib
import json
import os
from pathlib import Path

from auditor import audit_result, load_frozen_cases


ROOT = Path(__file__).resolve().parent
RESULTS = Path(os.environ.get("AI5504_RESULTS_DIR", ROOT / "results" / "t0"))
INPUT = RESULTS / "candidate.json"
OUTPUT = RESULTS / "audit.json"


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
    freeze = verify_frozen_sources()
    if not INPUT.is_file():
        raise SystemExit("STOP_CANDIDATE_MISSING")
    if OUTPUT.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    candidate_bytes = INPUT.read_bytes()
    envelope = json.loads(candidate_bytes)
    result = envelope.get("candidate", {})
    audit = audit_result(result, load_frozen_cases(ROOT / "cases.json"))
    identity_errors = []
    if envelope.get("allocation") != freeze.get("allocation"):
        identity_errors.append("allocation_identity_mismatch")
    if envelope.get("image_digest") != freeze.get("container", {}).get("image_digest"):
        identity_errors.append("image_identity_mismatch")
    if not str(envelope.get("python", "")).startswith("3.12."):
        identity_errors.append("python_version_mismatch")
    errors = audit["errors"] + identity_errors
    report = {
        "decision": "PASS" if not errors else "FAIL",
        "errors": errors,
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "corpus_sha256": result.get("corpus_sha256"),
    }
    with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical(report) + "\n")
    print(canonical(report))
    if report["decision"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
