"""Raw-only independent reconstruction; intentionally does not import candidate.py or ledger.py."""
import copy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXPECTED = {"SPACE", "W"}


def reconstruct(rows):
    if not isinstance(rows, list):
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["rows_not_list"]}
    keys = [r for r in rows if isinstance(r, dict) and r.get("kind") == "key_interval"]
    terminals = [r for r in rows if isinstance(r, dict) and r.get("kind") == "verified_empty"]
    if (len(keys) + len(terminals) != len(rows) or not keys or len(terminals) != 1
            or {r.get("key") for r in keys} != EXPECTED
            or len({r.get("key") for r in keys}) != len(keys)):
        return {"status": "UNKNOWN", "intervals": [],
                "reasons": ["expected_key_inventory_mismatch"]}
    action, epoch = keys[0].get("action_id"), keys[0].get("epoch")
    intervals = []
    for row in keys:
        if (row.get("action_id") != action or type(row.get("epoch")) is not int
                or row.get("epoch") != epoch or row.get("source") != "input-owner-v11"):
            return {"status": "UNKNOWN", "intervals": [], "reasons": ["identity_or_source"]}
        fields = ("press_request_ns", "press_sync_ns", "down_sample_ns",
                  "release_request_ns", "release_sync_ns", "up_sample_ns")
        vals = [row.get(f) for f in fields]
        if any(type(v) is not int or v < 0 for v in vals):
            return {"status": "UNKNOWN", "intervals": [], "reasons": ["invalid_timestamp"]}
        p0, p1, down, r0, r1, up = vals
        if not (p0 <= p1 <= down < r0 <= r1 <= up):
            return {"status": "UNKNOWN", "intervals": [], "reasons": ["timestamp_order"]}
        intervals.append({"action_id": action, "epoch": epoch, "key": row["key"],
                          "lower_ns": r0 - p1, "upper_ns": r1 - p0})
    end = terminals[0]
    t = end.get("timestamp_ns")
    if (end.get("action_id") != action or type(end.get("epoch")) is not int
            or end.get("epoch") != epoch or end.get("source") != "xquerykeymap"
            or end.get("keys_down") != [] or type(t) is not int
            or any(r["up_sample_ns"] > t for r in keys)):
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["terminal_invalid"]}
    return {"status": "BOUNDED", "intervals": sorted(intervals, key=lambda x: x["key"]),
            "reasons": []}


def main():
    raw = json.loads((HERE / "raw.json").read_text(encoding="utf-8"))
    full = copy.deepcopy(raw["events"])
    omitted = [r for r in copy.deepcopy(full)
               if not (r.get("kind") == "key_interval" and r.get("key") == "SPACE")]
    result = {"allocation": "MAP01-PER-KEY-OCCUPANCY-COMPLETENESS-A01-20261005",
              "cases": {"complete": reconstruct(full), "space_row_omitted": reconstruct(omitted)},
              "independent": True}
    (HERE / "audit-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                            encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    ok = (result["cases"]["complete"]["status"] == "BOUNDED"
          and result["cases"]["space_row_omitted"]["status"] == "UNKNOWN")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
