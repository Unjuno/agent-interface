"""One-call boundary probe against the unchanged #6094 occupancy ledger."""
import hashlib
import json
from pathlib import Path

from ledger_under_test import summarize

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture.json"
OUT = HERE / "results" / "t0-01" / "raw.json"


def main():
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes.decode("utf-8"))
    result = summarize(fixture["events"])
    payload = {
        "schema": "map01-repeated-key-pulse-occupancy-raw-v1",
        "allocation_id": "MAP01-REPEATED-KEY-PULSE-OCCUPANCY-59-T0-20261001-01",
        "main_sha": "f54e7665f099e78d11cff9ca28e812782aac33d1",
        "candidate_source_pr": 6094,
        "candidate_source_commit": "3983343f6773f118b92652c5e7f72a34b9eda7a2",
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "candidate_invocations": 1,
        "retries": 0,
        "candidate_result": result,
    }
    encoded = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(encoded, encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
