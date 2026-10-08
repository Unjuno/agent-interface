import argparse
import hashlib
import json
import re

EXPECTED = {
    "v38": {"sha256": "80b964c9ab7d86fbd0b2bc56957157e018e9dbb90457f286995a2e6036192bc3", "rows": 340, "input_admission": 11, "keys_held": 11, "input_released": 0, "terminal": 7},
    "v39": {"sha256": "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381", "rows": 634, "input_admission": 39, "keys_held": 28, "input_released": 1, "terminal": 9},
}
SOURCE_COMMIT = "f65b39b6434714a08dfa743f8a16f5cae1667f6d"

def analyze(label, path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected = EXPECTED[label]
    assert digest == expected["sha256"], (label, "source SHA mismatch", digest)
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    counts = {}
    for row in rows:
        event = row.get("event", "<missing>")
        counts[event] = counts.get(event, 0) + 1
    assert len(rows) == expected["rows"], (label, "row count mismatch", len(rows))
    for event in ("input_admission", "keys_held", "input_released", "terminal"):
        assert counts.get(event, 0) == expected[event], (label, event, counts.get(event, 0))
    direct_edge_markers = re.findall(r"(?i)key.?up|key.?release|actuation.?id|physical.?edge", raw.decode("utf-8"))
    terminals = [row for row in rows if row.get("event") == "terminal"]
    verified_empty = [row for row in terminals if row.get("release", {}).get("event") == "owner_release"
                      and row["release"].get("verified") is True
                      and row["release"].get("keys_down") == []
                      and row["release"].get("buttons_down") == []
                      and isinstance(row["release"].get("verified_ns"), int)]
    assert len(verified_empty) == expected["terminal"]
    assert not direct_edge_markers
    return {"file": path.name, "sha256": digest, "event_rows": len(rows),
            "event_counts": {key: counts.get(key, 0) for key in ("input_admission", "keys_held", "input_released", "terminal")},
            "terminal_verified_empty": len(verified_empty),
            "direct_normal_key_up_or_actuation_markers": len(direct_edge_markers),
            "interpretation": "key-down admission/held acknowledgements and terminal verified-empty bounds exist; ordinary per-key key-up timestamps are absent"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("v38_events")
    parser.add_argument("v39_events")
    args = parser.parse_args()
    value = {"schema": "retained-map01-input-edge-inventory-v1", "source_commit": SOURCE_COMMIT,
             "runs": [analyze("v38", __import__("pathlib").Path(args.v38_events)),
                      analyze("v39", __import__("pathlib").Path(args.v39_events))]}
    print(json.dumps(value, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
