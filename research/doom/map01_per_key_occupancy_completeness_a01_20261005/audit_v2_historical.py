"""Independent raw-only v2 audit of legacy omission acceptance and completeness gate."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def legacy_reconstruct(rows):
    """Reconstruct selected v1 ledger semantics without importing its implementation."""
    if not isinstance(rows, list):
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["rows_not_list"]}
    keyed = [r for r in rows if isinstance(r, dict) and r.get("kind") == "key_interval"]
    empty = [r for r in rows if isinstance(r, dict) and r.get("kind") == "verified_empty"]
    if len(keyed) + len(empty) != len(rows) or not keyed or len(empty) != 1:
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["row_or_terminal_count"]}
    action, epoch = keyed[0].get("action_id"), keyed[0].get("epoch")
    result = []
    seen = set()
    for row in keyed:
        key = row.get("key")
        fields = ("press_request_ns", "press_sync_ns", "down_sample_ns",
                  "release_request_ns", "release_sync_ns", "up_sample_ns")
        vals = [row.get(f) for f in fields]
        if (key in seen or not isinstance(key, str) or not key or row.get("action_id") != action
                or type(row.get("epoch")) is not int or row.get("epoch") != epoch
                or row.get("source") != "input-owner-v11"
                or any(type(v) is not int or v < 0 for v in vals)):
            return {"status": "UNKNOWN", "intervals": [], "reasons": ["key_row_invalid"]}
        seen.add(key)
        p0, p1, down, r0, r1, up = vals
        if not (p0 <= p1 <= down < r0 <= r1 <= up):
            return {"status": "UNKNOWN", "intervals": [], "reasons": ["timestamp_order"]}
        result.append({"action_id": action, "epoch": epoch, "key": key,
                       "lower_ns": r0 - p1, "upper_ns": r1 - p0})
    terminal = empty[0]
    stamp = terminal.get("timestamp_ns")
    if (terminal.get("action_id") != action or type(terminal.get("epoch")) is not int
            or terminal.get("epoch") != epoch or terminal.get("source") != "xquerykeymap"
            or terminal.get("keys_down") != [] or type(stamp) is not int
            or any(row.get("up_sample_ns", stamp + 1) > stamp for row in keyed)):
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["terminal_invalid"]}
    return {"status": "BOUNDED", "intervals": sorted(result, key=lambda x: x["key"]),
            "reasons": []}


def complete_reconstruct(rows, expected):
    result = legacy_reconstruct(rows)
    if result["status"] != "BOUNDED":
        return result
    observed = {row["key"] for row in result["intervals"]}
    if observed != set(expected):
        return {"status": "UNKNOWN", "intervals": [],
                "reasons": ["expected_key_inventory_mismatch"]}
    return result


def main():
    raw_path = HERE / "raw.json"
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    full = copy.deepcopy(raw["events"])
    missing_space = [r for r in copy.deepcopy(full)
                     if not (r.get("kind") == "key_interval" and r.get("key") == "SPACE")]
    expected = {"SPACE", "W"}
    legacy_full = legacy_reconstruct(full)
    legacy_missing = legacy_reconstruct(missing_space)
    gated_full = complete_reconstruct(full, expected)
    gated_missing = complete_reconstruct(missing_space, expected)
    checks = {
        "legacy_full_preserves_original_bounds": legacy_full["status"] == "BOUNDED"
            and {r["key"]: (r["lower_ns"], r["upper_ns"]) for r in legacy_full["intervals"]}
                == {"SPACE": (32, 50), "W": (70, 90)},
        "legacy_accepts_missing_space": legacy_missing["status"] == "BOUNDED"
            and [r["key"] for r in legacy_missing["intervals"]] == ["W"],
        "gate_preserves_complete_case": gated_full == legacy_full,
        "gate_rejects_missing_space": gated_missing["status"] == "UNKNOWN"
            and gated_missing["reasons"] == ["expected_key_inventory_mismatch"]
            and gated_missing["intervals"] == [],
        "source_manifest_is_expected_fixture": expected == {"SPACE", "W"},
    }
    report = {"allocation": "MAP01-PER-KEY-OCCUPANCY-COMPLETENESS-A01-20261005",
              "status": "PASS_METHOD_SCOPED" if all(checks.values()) else "FAIL_AUDIT",
              "checks": checks,
              "legacy_complete": legacy_full,
              "legacy_space_row_omitted": legacy_missing,
              "gated_complete": gated_full,
              "gated_space_row_omitted": gated_missing,
              "expected_keys": sorted(expected),
              "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "imports_candidate_or_legacy_code": False,
              "scope": "deterministic synthetic evidence mutation; no live input, effect, recovery, or resource claim"}
    out = HERE / "audit-result-v2.json"
    out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
