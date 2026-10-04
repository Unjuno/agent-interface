"""Pinned, raw-only v3 audit of legacy omission acceptance and completeness gate."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def validate_pins(raw_bytes, audit_bytes, freeze):
    """Validate frozen evidence/source digests and the predeclared key inventory."""
    checks = {
        "raw_matches_frozen_digest": sha256(raw_bytes) == freeze.get("input_sha256"),
        "audit_matches_frozen_digest": sha256(audit_bytes) == freeze.get("audit_v3_sha256"),
    }
    expected = freeze.get("expected_keys")
    valid_inventory = (isinstance(expected, list) and bool(expected)
                       and all(isinstance(key, str) and key for key in expected)
                       and len(expected) == len(set(expected)))
    checks["frozen_expected_inventory_is_valid"] = valid_inventory
    return checks, set(expected) if valid_inventory else set()


def legacy_reconstruct(rows):
    """Reconstruct selected v1 ledger semantics without importing its implementation."""
    if not isinstance(rows, list):
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["rows_not_list"]}
    keyed = [r for r in rows if isinstance(r, dict) and r.get("kind") == "key_interval"]
    empty = [r for r in rows if isinstance(r, dict) and r.get("kind") == "verified_empty"]
    if len(keyed) + len(empty) != len(rows) or not keyed or len(empty) != 1:
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["row_or_terminal_count"]}
    action, epoch = keyed[0].get("action_id"), keyed[0].get("epoch")
    result, seen = [], set()
    for row in keyed:
        key = row.get("key")
        fields = ("press_request_ns", "press_sync_ns", "down_sample_ns",
                  "release_request_ns", "release_sync_ns", "up_sample_ns")
        vals = [row.get(field) for field in fields]
        if (key in seen or not isinstance(key, str) or not key or row.get("action_id") != action
                or type(row.get("epoch")) is not int or row.get("epoch") != epoch
                or row.get("source") != "input-owner-v11"
                or any(type(value) is not int or value < 0 for value in vals)):
            return {"status": "UNKNOWN", "intervals": [], "reasons": ["key_row_invalid"]}
        seen.add(key)
        p0, p1, down, r0, r1, up = vals
        if not (p0 <= p1 <= down < r0 <= r1 <= up):
            return {"status": "UNKNOWN", "intervals": [], "reasons": ["timestamp_order"]}
        result.append({"action_id": action, "epoch": epoch, "key": key,
                       "lower_ns": r0 - p1, "upper_ns": r1 - p0})
    terminal, stamp = empty[0], empty[0].get("timestamp_ns")
    if (terminal.get("action_id") != action or type(terminal.get("epoch")) is not int
            or terminal.get("epoch") != epoch or terminal.get("source") != "xquerykeymap"
            or terminal.get("keys_down") != [] or type(stamp) is not int
            or any(row.get("up_sample_ns", stamp + 1) > stamp for row in keyed)):
        return {"status": "UNKNOWN", "intervals": [], "reasons": ["terminal_invalid"]}
    return {"status": "BOUNDED", "intervals": sorted(result, key=lambda item: item["key"]),
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
    raw_path, freeze_path = HERE / "raw.json", HERE / "AUDIT_V3_FREEZE.json"
    raw_bytes, freeze = raw_path.read_bytes(), json.loads(freeze_path.read_text(encoding="utf-8"))
    audit_bytes = Path(__file__).read_bytes()
    pin_checks, expected = validate_pins(raw_bytes, audit_bytes, freeze)
    if not all(pin_checks.values()):
        report = {"allocation": freeze.get("allocation"), "status": "FAIL_AUDIT_PINS",
                  "pin_checks": pin_checks, "expected_keys": sorted(expected)}
        (HERE / "audit-result-v3.json").write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        raise SystemExit(1)
    raw = json.loads(raw_bytes.decode("utf-8"))
    full = copy.deepcopy(raw["events"])
    missing = [row for row in copy.deepcopy(full)
               if not (row.get("kind") == "key_interval" and row.get("key") == "SPACE")]
    legacy_full, legacy_missing = legacy_reconstruct(full), legacy_reconstruct(missing)
    gated_full, gated_missing = complete_reconstruct(full, expected), complete_reconstruct(missing, expected)
    checks = {
        **pin_checks,
        "legacy_full_preserves_original_bounds": legacy_full["status"] == "BOUNDED"
            and {r["key"]: (r["lower_ns"], r["upper_ns"]) for r in legacy_full["intervals"]}
                == {"SPACE": (32, 50), "W": (70, 90)},
        "legacy_accepts_missing_space": legacy_missing["status"] == "BOUNDED"
            and [r["key"] for r in legacy_missing["intervals"]] == ["W"],
        "gate_preserves_complete_case": gated_full == legacy_full,
        "gate_rejects_missing_space": gated_missing["status"] == "UNKNOWN"
            and gated_missing["reasons"] == ["expected_key_inventory_mismatch"]
            and gated_missing["intervals"] == [],
        "observed_inventory_matches_freeze":
            {row["key"] for row in legacy_full["intervals"]} == expected,
    }
    report = {"allocation": freeze["allocation"],
              "status": "PASS_METHOD_SCOPED" if all(checks.values()) else "FAIL_AUDIT",
              "checks": checks, "legacy_complete": legacy_full,
              "legacy_space_row_omitted": legacy_missing,
              "gated_complete": gated_full, "gated_space_row_omitted": gated_missing,
              "expected_keys": sorted(expected), "raw_sha256": sha256(raw_bytes),
              "audit_v3_sha256": sha256(audit_bytes),
              "imports_candidate_or_legacy_code": False,
              "scope": "deterministic synthetic evidence mutation; no live input, effect, recovery, or resource claim"}
    (HERE / "audit-result-v3.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
