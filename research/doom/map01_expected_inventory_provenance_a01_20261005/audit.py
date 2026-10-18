"""Raw-only audit; does not import the candidate or the legacy ledger."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw_bytes = (HERE / "raw.json").read_bytes()
raw = json.loads(raw_bytes.decode("utf-8"))
rows = raw["events"]
intervals = [row for row in rows if row.get("kind") == "key_interval"]
original_keys = sorted(row.get("key") for row in intervals)
omitted = [row for row in intervals if row.get("key") != "SPACE"]
omitted_keys = sorted(row.get("key") for row in omitted)
outcome = json.loads((HERE / "experiment-output.json").read_text(encoding="utf-8"))
cases = outcome["cases"]
checks = {
    "raw_fixture_contains_two_distinct_keys": original_keys == ["SPACE", "W"],
    "mutated_observation_contains_only_w": omitted_keys == ["W"],
    "complete_default_control_is_bounded": cases["complete_correct_inventory"]["status"] == "BOUNDED",
    "omission_with_correct_inventory_is_unknown": cases["omitted_correct_inventory"]["status"] == "UNKNOWN",
    "omission_with_underdeclared_inventory_is_bounded": (
        cases["omitted_underdeclared_inventory"]["status"] == "BOUNDED"
        and cases["omitted_underdeclared_inventory"]["intervals"] == [
            {"action_id": "act-1", "epoch": 7, "key": "W", "lower_ns": 70, "upper_ns": 90}
        ]
    ),
    "complete_with_underdeclared_inventory_is_unknown": (
        cases["complete_underdeclared_inventory"]["status"] == "UNKNOWN"
    ),
}
report = {
    "allocation": "MAP01-EXPECTED-INVENTORY-PROVENANCE-A01-20261005",
    "status": "PASS" if all(checks.values()) else "FAIL_AUDIT",
    "checks": checks,
    "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "candidate_output_status": outcome["status"],
    "imports_candidate_or_ledger": False,
    "scope": "independent arithmetic/row-set audit; no admission-provenance source exists in the pinned fixture",
}
(HERE / "audit-output.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, sort_keys=True))
raise SystemExit(0 if all(checks.values()) else 1)
