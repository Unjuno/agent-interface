"""Build one candidate record from immutable Git blobs; never access live apps."""

import hashlib
import json
import pathlib
import sys

from coverage_transfer import build_coverage
from frozen_sources import load_inputs_from_payload


def build_result(root, payload):
    root = pathlib.Path(root).resolve()
    inputs, provenance = load_inputs_from_payload(payload)
    candidate = build_coverage(inputs["physical"], inputs["occupancy"], inputs["feedback"], inputs["calc"])
    raw = json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest_raw = json.dumps(provenance, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "decision": "CANDIDATE_RECONSTRUCTED",
        "source_provenance": provenance,
        "source_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate": candidate,
        "scope": "posthoc transfer coverage only",
    }


def main():
    root = pathlib.Path(__file__).resolve().parent
    if len(sys.argv) != 3 or sys.argv[1] != "--stdin":
        raise SystemExit("usage: run_once.py --stdin ALLOCATION_ID")
    allocation = sys.argv[2]
    if allocation != "t0-03":
        raise SystemExit("unknown allocation")
    output = root / "results" / allocation
    if output.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    output.mkdir(parents=True)
    record = build_result(root, sys.stdin.buffer.read())
    (output / "candidate.json").write_text(
        json.dumps(record["candidate"], sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (output / "run.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key != "candidate"}, sort_keys=True))


if __name__ == "__main__":
    main()
