"""Independent raw-only audit of mutable owner-release record A01."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
raw = json.loads((HERE / "results/formal_02/candidate.json").read_text(encoding="utf-8"))
OUT = HERE / "results/formal_02/audit.json"
if OUT.exists():
    raise SystemExit(f"refusing to overwrite frozen audit output: {OUT}")
assert raw["schema"] == "map01-v39-mutable-release-record-custody-a01-v1"
assert raw["source_sha256"] == {
    "input_owner_v13_candidate.py": "0e3c65aadfba76b644f1ca99afa267bc873bc120320a4b0cac67dafb82cfa814",
    "bridge_v2_candidate.py": "81e759b0484ac5b7854da0ebcffa917035f56b83a3dbfda40cafbb7f9f5138d1",
}
assert [case["case"] for case in raw["cases"]] == ["baseline", "neutral_revisit_probe"]
reports = {}
for case in raw["cases"]:
    label = case["case"]
    gate_records = case["snapshot_at_aggregate_gate"]
    final_records = case["final_owner_records"]
    assert len(gate_records) == len(final_records) == 1
    gate, final = gate_records[0], final_records[0]
    assert gate["event"] == final["event"] == "owner_release"
    assert gate["verified"] is False
    assert final["verified"] is True and final["keys_down"] == [] and final["buttons_down"] == []
    assert gate["per_key_release_measurements"] == final["per_key_release_measurements"]
    rows = [row for row in case["events_after_partial_drain"] if row.get("event") == "input_release_measurement"]
    admissions = [row for row in case["events_after_partial_drain"] if row.get("event") == "input_admission"]
    assert len(admissions) == len(rows) == 1
    assert admissions[0]["physical_key_measurement"]["classification"] == "CONFIRMED_PHYSICAL_DOWN"
    down_id = admissions[0]["physical_key_measurement"]["actuation_id"]
    up_measurement = rows[0]["physical_key_measurement"]
    assert up_measurement["classification"] == "PHYSICAL_SAMPLE_UNAVAILABLE"
    assert up_measurement["actuation_id"] == down_id
    assert rows[0]["id"] == admissions[0]["id"] and rows[0]["step"] == admissions[0]["step"]
    assert not any(row["physical_key_measurement"]["classification"] == "CONFIRMED_PHYSICAL_UP"
                   for row in case["events_after_final_drain"] if row.get("event") == "input_release_measurement")
    assert case["final_owner_held_codes"] == [] and case["final_fake_physical_keys"] == []
    assert case["final_cursor"] == case["cursor_after_partial_drain"] == 1
    if label == "baseline":
        assert case["held_after_partial_drain"] == ["F8"]
        assert case["final_bridge_held"] == ["F8"]
        assert case["final_drain_added_event_count"] == 0
        status = "FAIL_REPRODUCED_MUTABLE_RECORD_CUSTODY"
    else:
        assert case["held_after_partial_drain"] == ["F8"]
        assert case["final_bridge_held"] == []
        assert case["final_drain_added_event_count"] == 0
        status = "PASS_DIAGNOSTIC_NEUTRAL_STATE_REVISIT_SCOPED"
    reports[label] = {
        "status": status,
        "owner_record_mutated_in_place_to_verified_empty": True,
        "partial_row_emitted_once": True,
        "confirmed_physical_up_fabricated": False,
        "final_bridge_held": case["final_bridge_held"],
        "final_owner_held_codes": case["final_owner_held_codes"],
    }
report = {
    "schema": "map01-v39-mutable-release-record-custody-a01-audit-v1",
    "cases_recomputed": reports,
    "scope": "raw-only source-bound fake-display mutable-record schedule; no candidate rerun",
    "mismatches": [],
}
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(report, sort_keys=True))
