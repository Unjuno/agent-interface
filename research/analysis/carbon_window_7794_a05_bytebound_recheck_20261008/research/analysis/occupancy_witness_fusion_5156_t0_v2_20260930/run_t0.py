"""One deterministic finite construction run; writes the first raw outcome."""

import itertools
import json
from pathlib import Path

from fusion import fuse


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "t0-02" / "raw.json"
DOMAIN = range(5)
IDENTITY = {
    "owner_id": "owner-1",
    "actuation_id": "act-1",
    "keycode": 38,
    "display_id": "display-1",
    "clock_id": "mono-ns-1",
}
FIELDS = tuple(IDENTITY)


def intervals():
    return [(a, b) for a in DOMAIN for b in DOMAIN if a <= b]


def make_record(down, up, start, returned, sync):
    return {
        "identity": dict(IDENTITY),
        "down_query": {**IDENTITY, "query": list(down)},
        "up_query": {**IDENTITY, "query": list(up)},
        "owner_release": {
            **IDENTITY,
            "request_start": start,
            "request_return": returned,
            "sync_return": sync,
            "release_count": 1,
            "repress_count": 0,
        },
    }


def main():
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    rows = []
    brackets = [(a, b, c) for a, b, c in itertools.combinations_with_replacement(DOMAIN, 3)]
    for down, up, (start, returned, sync) in itertools.product(intervals(), intervals(), brackets):
        record = make_record(down, up, start, returned, sync)
        rows.append({"case_id": f"valid-{len(rows):05d}", "record": record, "candidate": fuse(record)})

    corruptions = []
    for field in FIELDS:
        row = make_record((0, 1), (3, 4), 1, 2, 3)
        row["up_query"][field] = f"tampered-{field}"
        corruptions.append((f"identity-{field}", row))
    row = make_record((0, 1), (3, 4), 1, 2, 3)
    del row["down_query"]
    corruptions.append(("missing-down-witness", row))
    row = make_record((0, 1), (3, 4), 1, 2, 3)
    row["owner_release"]["release_count"] = 2
    corruptions.append(("duplicate-release", row))
    row = make_record((0, 1), (3, 4), 1, 2, 3)
    row["owner_release"]["repress_count"] = 1
    corruptions.append(("repress", row))
    row = make_record((0, 1), (3, 4), 1, 2, 3)
    row["identity"]["keycode"] = True
    for source in (row["down_query"], row["up_query"], row["owner_release"]):
        source["keycode"] = True
    corruptions.append(("malformed-shared-identity", row))
    row = make_record((0, 1), (3, 4), 1, 2, 3)
    row["owner_release"]["release_count"] = True
    corruptions.append(("boolean-release-count", row))
    row = make_record((0, 1), (3, 4), 1, 2, 3)
    row["identity"].pop("clock_id")
    corruptions.append(("missing-clock-identity", row))
    row = make_record((0, True), (3, 4), 1, 2, 3)
    corruptions.append(("boolean-query-end", row))
    row = make_record((0, 1), (3, 4), 3, 2, 4)
    corruptions.append(("inverted-owner-order", row))
    row = make_record((0, 1), (3, 4), 1, 2, 3)
    row["down_query"]["query"] = [0, True]
    corruptions.append(("malformed-down-query", row))
    rows.extend({"case_id": name, "record": row, "candidate": fuse(row)} for name, row in corruptions)

    payload = {
        "task": "R133_OCCUPANCY_WITNESS_FUSION_5156_T0_V2_20260930_01",
        "domain": [0, 4],
        "valid_case_count": len(rows) - len(corruptions),
        "corruption_case_count": len(corruptions),
        "rows": rows,
        "authority_grants": 0,
        "network_calls": 0,
        "gui_input_calls": 0,
        "model_calls": 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=False)
    OUT.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "rows": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
