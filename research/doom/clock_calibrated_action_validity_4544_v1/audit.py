import copy

MAX_AGE_NS = 30_000_000_000

def audit(data):
    assert data["experiment"] == "clock_calibrated_action_validity_4544_v1"
    assert data["source_commit"] == "91b5143989403754b360738c445f72b68b673718"
    assert data["source_blobs"] == {
        "action_validity_admission_v1.py": "31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e",
        "running_action_guard_v1.py": "d54047e78bc76f53ef47c6f70fd4a3be6318f09c",
    }
    assert data["image"] == "issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e"
    assert data["platform"] == "linux/arm64" and data["network"] == "none"
    rows = data["samples"]
    assert len(rows) == 3
    lows, highs = [], []
    for row in rows:
        assert row["host_after_ns"] >= row["host_before_ns"]
        lows.append(row["host_before_ns"] - row["container_capture_ns"])
        highs.append(row["host_after_ns"] - row["container_capture_ns"])
    lower, upper = max(lows), min(highs)
    assert [lower, upper] == data["common_offset_host_minus_container_ns"]
    assert lower <= upper
    width = upper - lower
    assert width == data["uncertainty_ns"] <= 1_000_000_000
    decision = data["controller_decided_ns"]
    raw = rows[-1]["container_capture_ns"]
    translated = raw + lower
    assert translated == rows[-1]["host_before_ns"]
    assert data["max_current_age_ns"] == MAX_AGE_NS
    cases = data["rows"]
    assert [x["case"] for x in cases] == [
        "raw_mixed_domain", "conservative_same_session_translation",
        "translated_31s_older_control"]
    expected = [
        (raw, "REJECTED_STALE", "CANCEL_REQUIRED", False, True),
        (translated, "VALID_CURRENT", "INPUT_ACTIVE", True, False),
        (translated - 31_000_000_000, "REJECTED_STALE", "CANCEL_REQUIRED", False, True),
    ]
    for row, (capture, status, state, authority, new_decision) in zip(cases, expected):
        assert row["capture_ns"] == capture
        assert row["decision_ns"] == decision
        assert row["apparent_age_ns"] == decision - capture
        assert row["validity_status"] == status
        assert row["guard_state"] == state
        assert row["current_input_authority"] is authority
        assert row["requires_new_decision"] is new_decision
        if status == "REJECTED_STALE":
            assert row["validity_reason"] == "current_snapshot_too_old"
            assert row["invalidation_kind"] == "action_validity"
    assert cases[0]["apparent_age_ns"] > MAX_AGE_NS
    assert 0 <= cases[1]["apparent_age_ns"] <= MAX_AGE_NS
    assert cases[2]["apparent_age_ns"] > MAX_AGE_NS
    assert data["disposition"] == "PASS_SCOPED"
    return True

def corruption_controls(data):
    for mutation in (
        lambda x: x["samples"][0].update(host_after_ns=x["samples"][0]["host_before_ns"]-1),
        lambda x: x["common_offset_host_minus_container_ns"].reverse(),
        lambda x: x["rows"][1].update(current_input_authority=False),
        lambda x: x["rows"][2].update(validity_status="VALID_CURRENT"),
    ):
        changed = copy.deepcopy(data)
        mutation(changed)
        try:
            audit(changed)
        except AssertionError:
            continue
        raise AssertionError("corruption was accepted")
    return 4

if __name__ == "__main__":
    import json, pathlib
    result = json.loads(pathlib.Path(__file__).with_name("result.json").read_text())
    assert audit(result)
    print(f"PASS_INDEPENDENT_AUDIT corruption_rejections={corruption_controls(result)}")
