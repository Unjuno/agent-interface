import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    "v38-events.jsonl": {
        "sha256": "80b964c9ab7d86fbd9bb2bc56957157e018e9dbb90457f286995a2e6036192bc3",
        "rows": 340,
        "input_admission": 11,
        "keys_held": 11,
        "input_released": 0,
        "terminal": 7,
    },
    "v39-events.jsonl": {
        "sha256": "2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381",
        "rows": 634,
        "input_admission": 39,
        "keys_held": 28,
        "input_released": 1,
        "terminal": 9,
    },
}
result = {
    "schema": "retained-map01-input-edge-inventory-v1",
    "source_commit": "f65b39b6434714a08dfa743f8a16f5cae1667f6d",
    "runs": [],
}
for name, expected in EXPECTED.items():
    raw = (ROOT / name).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == expected["sha256"], (name, digest)
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    counts = {}
    for row in rows:
        event = row.get("event", "<missing>")
        counts[event] = counts.get(event, 0) + 1
    assert len(rows) == expected["rows"]
    for event in ("input_admission", "keys_held", "input_released", "terminal"):
        assert counts.get(event, 0) == expected[event], (name, event, counts.get(event, 0))
    text = raw.decode("utf-8")
    direct_edge_markers = re.findall(r"(?i)key.?up|key.?release|actuation.?id|physical.?edge", text)
    terminals = [row for row in rows if row.get("event") == "terminal"]
    verified_empty = [
        row for row in terminals
        if row.get("release", {}).get("event") == "owner_release"
        and row["release"].get("verified") is True
        and row["release"].get("keys_down") == []
        and row["release"].get("buttons_down") == []
        and isinstance(row["release"].get("verified_ns"), int)
    ]
    assert len(verified_empty) == expected["terminal"], (name, len(verified_empty))
    releases = [row for row in rows if row.get("event") == "input_released"]
    assert all(isinstance(row.get("owner_release", {}).get("verified_ns"), int) for row in releases)
    assert not direct_edge_markers, (name, direct_edge_markers[:5])
    result["runs"].append({
        "file": name,
        "sha256": digest,
        "event_rows": len(rows),
        "event_counts": {key: counts.get(key, 0) for key in
                         ("input_admission", "keys_held", "input_released", "terminal")},
        "terminal_verified_empty": len(verified_empty),
        "direct_normal_key_up_or_actuation_markers": len(direct_edge_markers),
        "interpretation": "key-down admission/held acknowledgements and terminal verified-empty bounds exist; ordinary per-key key-up timestamps are absent"
    })
print(json.dumps(result, sort_keys=True, indent=2))
