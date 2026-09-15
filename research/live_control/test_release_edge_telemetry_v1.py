import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "release_edge", HERE / "release_edge_telemetry_v1.py")
release_edge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_edge)


def clock(values):
    iterator = iter(values)
    return lambda: next(iterator)


def bitmap_with(*keycodes):
    value = bytearray(32)
    for code in keycodes:
        value[code // 8] |= 1 << (code % 8)
    return value


def test_release_call_records_request_and_post_sync_return_bracket():
    called = []
    row = release_edge.time_release_call(
        "a", lambda: called.append("released"), clock([100, 125]))
    assert called == ["released"]
    assert row == {
        "key": "a",
        "release_call_requested_ns": 100,
        "post_sync_call_return_ns": 125,
        "call_bracket_ns": 25,
    }


def test_keymap_decode_only_reports_selected_down_keys():
    down = release_edge.keys_down_from_bitmap(
        bitmap_with(38, 65), {"a": 38, "space": 65, "d": 40})
    assert down == ["a", "space"]


def test_multikey_batch_samples_once_after_all_releases():
    samples = []
    releases = [
        {"key": "a", "release_call_requested_ns": 100,
         "post_sync_call_return_ns": 110, "call_bracket_ns": 10},
        {"key": "space", "release_call_requested_ns": 111,
         "post_sync_call_return_ns": 120, "call_bracket_ns": 9},
    ]

    def sample():
        samples.append("sampled")
        return bitmap_with()

    row = release_edge.finalize_release_batch(
        releases, sample, {"a": 38, "space": 65}, clock([121, 125]))
    assert samples == ["sampled"]
    assert row["release_batch_first_requested_ns"] == 100
    assert row["release_batch_last_post_sync_return_ns"] == 120
    assert row["x11_sample_started_ns"] == 121
    assert row["x11_sample_finished_ns"] == 125
    assert row["x11_keys_down_after_release"] == []
    assert row["x11_all_released_after_batch"] is True


def test_post_release_sample_can_retain_nonempty_state_without_faking_success():
    releases = [{"key": "a", "release_call_requested_ns": 100,
                 "post_sync_call_return_ns": 110, "call_bracket_ns": 10}]
    row = release_edge.finalize_release_batch(
        releases, lambda: bitmap_with(38), {"a": 38}, clock([111, 112]))
    assert row["x11_keys_down_after_release"] == ["a"]
    assert row["x11_all_released_after_batch"] is False


def test_sample_must_begin_after_last_release_return():
    releases = [{"key": "a", "release_call_requested_ns": 100,
                 "post_sync_call_return_ns": 120, "call_bracket_ns": 20}]
    try:
        release_edge.finalize_release_batch(
            releases, lambda: bitmap_with(), {"a": 38}, clock([119, 121]))
    except AssertionError as error:
        assert "before release calls returned" in str(error)
    else:
        raise AssertionError("pre-return sample must fail closed")


def test_overlapping_release_rows_fail_closed():
    releases = [
        {"key": "a", "release_call_requested_ns": 100,
         "post_sync_call_return_ns": 120, "call_bracket_ns": 20},
        {"key": "space", "release_call_requested_ns": 119,
         "post_sync_call_return_ns": 130, "call_bracket_ns": 11},
    ]
    try:
        release_edge.finalize_release_batch(
            releases, lambda: bitmap_with(), {"a": 38, "space": 65},
            clock([131, 132]))
    except ValueError as error:
        assert "not sequential" in str(error)
    else:
        raise AssertionError("overlapping release rows must fail closed")


def test_release_failure_propagates_without_success_receipt():
    def fail():
        raise RuntimeError("release failed")

    try:
        release_edge.time_release_call("a", fail, clock([100, 120]))
    except RuntimeError as error:
        assert str(error) == "release failed"
    else:
        raise AssertionError("release failure must propagate")


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} tests")
