from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def load_base_probe():
    path = ROOT / "research/doom/map01_release_receipt_repair_59_t1_a01_20261004/probe.py"
    spec = importlib.util.spec_from_file_location("release_receipt_a01_probe", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_case(failure_point):
    base = load_base_probe()
    fixture = base.load_fixture()
    source = (ROOT / "research/live_control/input_owner_v10.py").read_text(encoding="utf-8")
    owner_type = base.load_owners(source, (ROOT / "research/live_control/input_owner_v11.py").read_text(encoding="utf-8"))
    fixture.KEYMAP = {ord("W"): 77}
    fixture.SERVER["down"].clear()
    xtest = sys.modules["Xlib.ext.xtest"]
    original_input = xtest.fake_input
    original_sync = fixture.FakeDisplay.sync
    trace = {"release_attempts": 0, "sync_attempts": 0, "injected": False}

    def fake_input(display, event, code, **kwargs):
        xlib = sys.modules["Xlib"]
        if event == xlib.X.KeyRelease:
            trace["release_attempts"] += 1
            if failure_point == "xtest_before_apply" and not trace["injected"]:
                trace["injected"] = True
                raise OSError("injected XTest failure before fixture apply")
        return original_input(display, event, code, **kwargs)

    def sync(display):
        trace["sync_attempts"] += 1
        result = original_sync(display)
        if failure_point == "xsync_after_apply" and trace["release_attempts"] == 1 and not trace["injected"]:
            trace["injected"] = True
            raise OSError("injected XSync exception after fixture apply")
        return result

    xtest.fake_input = fake_input
    fixture.FakeDisplay.sync = sync
    owner = owner_type(":fake")
    lease = fixture.Lease()
    try:
        admission = owner.call("down", lease, "W")
        trace.update(release_attempts=0, sync_attempts=0, injected=False)
        failed_call = None
        try:
            owner.call("up", lease, "W")
        except Exception as exc:
            failed_call = {"type": type(exc).__name__, "message": str(exc)}
        else:
            raise AssertionError("injected failure unexpectedly returned a receipt")
        after_failure = {
            "fake_server_key_down": 77 in fixture.SERVER["down"],
            "trace": dict(trace),
        }
        retry_receipt = owner.call("up", lease, "W")
        after_retry = {
            "fake_server_key_down": 77 in fixture.SERVER["down"],
            "trace": dict(trace),
        }
        return {"failure_point": failure_point, "admission": admission,
                "failed_call": failed_call, "after_failure": after_failure,
                "retry_receipt": retry_receipt, "after_retry": after_retry}
    finally:
        owner.close()
        xtest.fake_input = original_input
        fixture.FakeDisplay.sync = original_sync


def main():
    for path, expected in FREEZE["sources"].items():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError((path, actual, expected))
    return {
        "schema": "map01-release-receipt-failure-boundary-result-v1",
        "status": "PASS_SCOPED",
        "cases": [run_case("xtest_before_apply"), run_case("xsync_after_apply")],
        "scope": FREEZE["scope"],
    }


if __name__ == "__main__":
    result = main()
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
