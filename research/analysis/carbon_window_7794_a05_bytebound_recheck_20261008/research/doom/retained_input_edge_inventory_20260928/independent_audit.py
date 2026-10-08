import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

EXPECTED = {
 "v38-events.jsonl": ("80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3", 340, {"input_admission":11,"keys_held":11,"input_released":0,"terminal":7}),
 "v39-events.jsonl": ("2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381", 634, {"input_admission":39,"keys_held":28,"input_released":1,"terminal":9}),
}

def walk(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield "key", key
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)
    elif isinstance(value, str):
        yield "value", value

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result_json")
    parser.add_argument("v38_events")
    parser.add_argument("v39_events")
    args = parser.parse_args()
    result = json.loads(Path(args.result_json).read_text(encoding="utf-8-sig"))
    assert result["schema"] == "retained-map01-input-edge-inventory-v1"
    assert result["source_commit"] == "f65b39b6434714a08dfa743f8a16f5cae1667f6d"
    runs = {row["file"]: row for row in result["runs"]}
    for filename, path in (("v38-events.jsonl", Path(args.v38_events)), ("v39-events.jsonl", Path(args.v39_events))):
        raw = path.read_bytes()
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
        sha, length, counts = EXPECTED[filename]
        observed = Counter(row.get("event") for row in rows)
        assert hashlib.sha256(raw).hexdigest() == sha == runs[filename]["sha256"]
        assert len(rows) == length == runs[filename]["event_rows"]
        for event, count in counts.items():
            assert observed[event] == count == runs[filename]["event_counts"][event]
        forbidden = [(kind, value) for row in rows for kind, value in walk(row)
                     if re.search(r"(?i)key.?up|actuation.?id|physical.?edge", value)]
        assert not forbidden, (filename, forbidden[:4])
        terminals = [row for row in rows if row.get("event") == "terminal"]
        good = [row for row in terminals if row.get("release", {}).get("verified") is True
                and row["release"].get("keys_down") == [] and row["release"].get("buttons_down") == []
                and isinstance(row["release"].get("verified_ns"), int)]
        assert len(good) == counts["terminal"] == runs[filename]["terminal_verified_empty"]
    print(json.dumps({"independent_audit":"PASS", "source_commit":result["source_commit"],
                      "verified_runs":["v38-events.jsonl","v39-events.jsonl"], "authority_or_task_claims":False}, indent=2))

if __name__ == "__main__":
    main()
