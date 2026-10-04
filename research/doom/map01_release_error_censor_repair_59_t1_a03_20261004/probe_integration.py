from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research/doom/map01_release_receipt_repair_59_t1_a01_20261004"))
import probe as base


def main():
    fixture = base.load_fixture()
    v10 = (ROOT / "research/live_control/input_owner_v10.py").read_text(encoding="utf-8")
    v11 = (ROOT / "research/live_control/input_owner_v11.py").read_text(encoding="utf-8")
    owner_type = base.load_owners(v10, v11)
    backend_type = base.load_typed_backend()
    fixture.KEYMAP = {ord("W"): 77}
    fixture.SERVER["down"].clear()
    xtest = sys.modules["Xlib.ext.xtest"]
    original_input = xtest.fake_input
    original_sync = fixture.FakeDisplay.sync
    trace = {"release_requests": 0, "sync_attempts": 0, "injected": False}

    def fake_input(display, event, code, **kwargs):
        if event == sys.modules["Xlib"].X.KeyRelease:
            trace["release_requests"] += 1
        return original_input(display, event, code, **kwargs)

    def sync(display):
        trace["sync_attempts"] += 1
        result = original_sync(display)
        if trace["release_requests"] == 1 and not trace["injected"]:
            trace["injected"] = True
            raise OSError("injected XSync exception after fake server applied KeyRelease")
        return result

    xtest.fake_input = fake_input
    fixture.FakeDisplay.sync = sync
    owner = owner_type(":fake")
    lease = fixture.Lease()
    backend = object.__new__(backend_type)
    backend.owner = owner
    backend.lease = lease
    backend.held = set()
    backend._input_event_context = ("failure-retry-plan", 0)
    backend.events = []
    backend.emit = backend.events.append
    try:
        backend.raw("W", True)
        trace["sync_attempts"] = 0
        backend._input_event_context = ("failure-retry-plan", 1)
        try:
            backend.raw("W", False)
            raise AssertionError("injected sync failure unexpectedly returned")
        except OSError:
            pass
        state_after_failure = {"fake_server_key_down": 77 in fixture.SERVER["down"],
                               "release_requests": trace["release_requests"]}
        backend._input_event_context = ("failure-retry-plan", 2)
        backend.raw("W", False)
        state_after_retry = {"fake_server_key_down": 77 in fixture.SERVER["down"],
                             "release_requests": trace["release_requests"]}
        cleanup = owner.call("release", lease)
        backend.events.append({"event": "input_released",
                               "intent_token": lease.intent_token,
                               "grants_input_authority": False,
                               "owner_release": cleanup})
        sys.path.insert(0, str(ROOT / "research/doom"))
        from map01_feedback_release_contract_v1 import reconcile_key_intervals
        intervals = reconcile_key_intervals(backend.events)
        return {"schema": "map01-release-error-censor-integration-result-v1",
                "status": "PASS_SCOPED",
                "events": backend.events,
                "state_after_unreceipted_failure": state_after_failure,
                "state_after_retry": state_after_retry,
                "release_trace": trace,
                "reconciled": intervals,
                "scope": "actual checked-out V10/V11, typed backend raw, and oracle under pinned FakeDisplay only"}
    finally:
        owner.close()
        xtest.fake_input = original_input
        fixture.FakeDisplay.sync = original_sync


if __name__ == "__main__":
    result = main()
    (HERE / "INTEGRATION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "events"}, indent=2))
