"""Audit preserved raw unittest output without importing the test package."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
raw = (HERE / "PRODUCTION_BARRIER_RAW.log").read_text()
decoder = json.JSONDecoder()
observations = []
for line in raw.splitlines():
    if "OBSERVATION " in line:
        try:
            row, _ = decoder.raw_decode(line.split("OBSERVATION ", 1)[1])
            observations.append(row)
        except json.JSONDecodeError:
            pass
assert "Ran 3 tests" in raw and "\nOK\n" in raw
assert len(observations) == 3
cases = {row["case"]: row for row in observations}
assert set(cases) == {
    "exact_candidate_baseline",
    "late_resample_treatment",
    "late_resample_retry_unavailable",
}

def measurement(row):
    return row["release"]["physical_key_measurement"]

for name in ("exact_candidate_baseline", "late_resample_retry_unavailable"):
    result = measurement(cases[name])
    assert result["classification"] == "PHYSICAL_SAMPLE_UNAVAILABLE"
    assert result["bracket"] is None

row = cases["late_resample_treatment"]
result = measurement(row)
assert result["classification"] == "CONFIRMED_PHYSICAL_UP"
assert result["identity_status"] == "RETIRED"
assert result["actuation_id"] == row["admission"]["physical_key_measurement"]["actuation_id"]
assert result["bracket"]["status"] == "CONFIRMED_PHYSICAL_UP"
assert result["bracket"]["physical_up_interval"] == [
    result["pre_sample"]["finished_ns"], result["post_sample"]["finished_ns"]
]
assert result["pre_sample"]["finished_ns"] <= result["release_request_ns"]
assert result["release_request_ns"] <= result["sync_return_ns"]
assert result["sync_return_ns"] <= result["post_sample"]["started_ns"]
for row in observations:
    assert row["record"]["verified"] is True
    assert row["record"]["keys_down"] == [] and row["record"]["buttons_down"] == []
    assert row["terminal"]["status"] == "needs_decision"
    assert row["terminal"]["release"]["verified"] is True
    for obj in (measurement(row), measurement(row).get("bracket") or {}):
        assert obj.get("grants_input_authority", False) is False
        assert obj.get("application_consumption_observed", False) is False
print("PASS: 3 raw cases; current-main release barrier; treatment interval and controls audited")
