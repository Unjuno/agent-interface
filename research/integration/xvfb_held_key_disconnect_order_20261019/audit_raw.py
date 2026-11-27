"""Verify the frozen Xvfb held-key disconnect-order receipt."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
R01_FILES = (
    RAW / "x11-held-key-disconnect-queue-run-39221315372.json",
    RAW / "x11-held-key-disconnect-queue-run-39221534890.json",
)
R02_FILE = RAW / "x11-held-key-disconnect-queue-run-39221822908.json"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    r01 = [read(path) for path in R01_FILES]
    for item in r01:
        assert item["status"] == "PASS_SCOPED_XVFB_HELD_KEY_ORDER"
        assert item["late_keypress_observed"] is False
        assert item["late_keypress_readback"]["keys_down"]["b"] is False
        # These runs did not preserve a pre-KeyRelease read and cannot be used
        # to attribute the release transition to the independent cleanup.
        assert "state_after_disconnect_before_release" not in item
        assert "independent_release_effect_observed" not in item

    r02 = read(R02_FILE)
    assert r02["schema"] == "agent-interface/xvfb-held-key-disconnect-queue-v2"
    assert r02["status"] == "PASS_SCOPED_XVFB_HELD_KEY_ORDER"
    assert r02["delay_ms"] == 8000
    assert r02["server_vendor"] == "The X.Org Foundation"
    assert r02["xres_version"] == [1, 2]
    assert r02["xtest_version"] == [2, 2]
    assert r02["disconnect_receipt"]["status"] == "disconnected"
    assert (r02["disconnect_receipt"]["expected_pid"]
            == r02["owner"]["pid"])
    assert (r02["disconnect_receipt"]["observed_pid"]
            != r02["owner"]["pid"])
    assert r02["initial_held_readback"]["keys_down"] == {
        "a": True, "b": False}
    assert r02["state_after_disconnect_before_release"]["keys_down"] == {
        "a": True, "b": False}
    assert r02["independent_release_effect_observed"] is True
    assert r02["release_readback_before_delay_horizon"]["keys_down"] == {
        "a": False, "b": False}
    assert r02["late_keypress_observed"] is False
    assert r02["late_keypress_readback"]["ms_after_owner_termination"] >= 8500
    assert r02["late_keypress_readback"]["keys_down"] == {
        "a": False, "b": False}
    assert r02["final_key_down"] == {"a": False, "b": False}
    assert r02["cleanup_status"] == "key_release_sync_completed"

    print(json.dumps({
        "status": "PASS_SCOPED_XVFB_HELD_KEY_ORDER",
        "r01_preliminary_runs": len(r01),
        "r01_late_b_observed": [x["late_keypress_observed"] for x in r01],
        "r02_owner_disconnect_ms": r02["disconnect_receipt"]["elapsed_ms"],
        "r02_release_transition": r02["independent_release_effect_observed"],
        "r02_late_b_observed": r02["late_keypress_observed"],
        "r02_keymap_after_horizon": r02["late_keypress_readback"]["keys_down"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
