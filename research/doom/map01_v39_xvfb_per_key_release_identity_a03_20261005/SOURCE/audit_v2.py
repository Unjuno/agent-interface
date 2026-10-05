"""Corrected independent auditor: incomplete candidate attempts classify STOP."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    raw = json.loads(args.raw.read_text())
    if digest(args.candidate) != freeze["candidate_sha256"]:
        raise SystemExit("candidate SHA mismatch")
    incomplete = (raw.get("status") != "CANDIDATE_COMPLETE" or bool(raw.get("errors")))
    result = {
        "schema": "map01-v39-xvfb-per-key-release-audit-a03-v2",
        "candidate_sha256": freeze["candidate_sha256"],
        "raw_sha256": digest(args.raw),
        "candidate_status": raw.get("status"),
        "client_event_count": len(raw.get("client_events", [])),
        "cleanup": raw.get("cleanup", {}),
        "errors": ["candidate stopped before a complete measurement; raw error retained"]
                  if incomplete else [],
        "decision": "STOP" if incomplete else "DEFER_TO_COMPLETE_AUDIT",
        "note": "No candidate rerun; an incomplete trace is not scored as a measurement mismatch.",
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"]}))


if __name__ == "__main__":
    main()
