"""One fresh X11/Tk case for Issue #869.

This runner is source-gated before starting Xvfb. Candidate cases execute the
exact current doom_typed_release_backend_v2.Backend.raw method with only its
parent class stubbed; the actual InputOwnerV11 and X11 path are real.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
import types

from Xlib import XK, display

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent
RESEARCH = LIVE.parent
DOOM = RESEARCH / "doom"
PINS = {
    LIVE / "input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    LIVE / "input_owner_v11.py": "842071284156d3ccc647f47135ee62a9e512cb56",
    DOOM / "doom_typed_release_backend_v2.py": "cf13d630ae22a50272a766c86d7f325f352a89d7",
}
HOLD_NS = 150_000_000


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def verify_sources() -> dict[str, str]:
    observed = {str(path.relative_to(RESEARCH)): git_blob_sha(path) for path in PINS}
    expected = {str(path.relative_to(RESEARCH)): sha for path, sha in PINS.items()}
    if observed != expected:
        raise RuntimeError(f"source drift: observed={observed!r} expected={expected!r}")
    return observed


def wait_display(name: str, deadline_s: float = 2.0):
    end = time.monotonic() + deadline_s
    last = None
    while time.monotonic() < end:
        try:
            return display.Display(name)
        except Exception as exc:  # setup-only retry
            last = exc
            time.sleep(0.02)
    raise RuntimeError(f"Xvfb unavailable: {last!r}")


def load_candidate_backend(owner, lease, case_id: str, emitted: list[dict]):
    # Load the exact v2 raw() implementation while avoiding unrelated DOOM/session
    # construction. This stub cannot perform input itself.
    parent = types.ModuleType("doom_typed_release_backend_v1")

    class Previous:
        pass

    parent.Backend = Previous
    parent.suite = object()
    sys.modules["doom_typed_release_backend_v1"] = parent
    spec = importlib.util.spec_from_file_location("release_edge_exact_v2", DOOM / "doom_typed_release_backend_v2.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    backend = object.__new__(module.Backend)
    backend._input_event_context = (case_id, 1)
    backend.owner = owner
    backend.lease = lease
    backend.held = set()
    backend.emit = emitted.append
    return backend


class Lease:
    def __init__(self, focus: int, token: str):
        self.expected_focus = focus
        self.deadline = time.perf_counter_ns() + 2_000_000_000
        self.cancel = threading.Event()
        self.focus_invalid = False
        self.intent_token = token

    def check(self) -> None:
        if time.perf_counter_ns() >= self.deadline:
            raise RuntimeError("lease expired")
        if self.cancel.is_set():
            raise RuntimeError("lease cancelled")


def run_case(case_id: str, arm: str, display_number: int, out: Path) -> dict:
    source_blobs = verify_sources()
    if out.exists():
        raise RuntimeError(f"exclusive output already exists: {out}")
    out.mkdir(parents=True)

    display_name = f":{display_number}"
    xauth = out / "empty.Xauthority"
    xauth.write_bytes(b"")
    env = os.environ.copy()
    env["DISPLAY"] = display_name
    env["XAUTHORITY"] = str(xauth)
    # python-xlib in this process consults os.environ, not only child env.
    os.environ["DISPLAY"] = display_name
    os.environ["XAUTHORITY"] = str(xauth)

    xvfb_log = open(out / "xvfb.log", "wb")
    receiver_out = open(out / "receiver.stdout", "wb")
    receiver_err = open(out / "receiver.stderr", "wb")
    xvfb = subprocess.Popen(
        ["Xvfb", display_name, "-screen", "0", "640x480x24", "-ac"],
        stdout=xvfb_log,
        stderr=subprocess.STDOUT,
        env=env,
    )
    receiver = None
    d = None
    owner = None
    try:
        d = wait_display(display_name)
        ready = out / "ready"
        event_log = out / "events.jsonl"
        receiver = subprocess.Popen(
            [sys.executable, str(HERE / "receiver.py"), "--log", str(event_log), "--ready", str(ready)],
            stdout=receiver_out,
            stderr=receiver_err,
            env=env,
        )
        deadline = time.monotonic() + 2.0
        while not ready.exists() and time.monotonic() < deadline:
            if receiver.poll() is not None:
                raise RuntimeError("receiver exited before ready")
            time.sleep(0.01)
        if not ready.exists():
            raise RuntimeError("receiver readiness timeout")

        focus = None
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            value = d.get_input_focus().focus
            ident = value.id if hasattr(value, "id") else value
            if isinstance(ident, int) and ident not in (0, 1):
                focus = ident
                break
            time.sleep(0.01)
        if focus is None:
            raise RuntimeError("no concrete focused Tk window")

        sys.path.insert(0, str(LIVE))
        token = f"release-edge-{case_id}"
        lease = Lease(focus, token)
        if arm == "baseline_v10":
            from input_owner_v10 import InputOwner

            owner = InputOwner(display_name)
            down_receipt = owner.call("down", lease, "F8")
            hold_started_ns = time.perf_counter_ns()
            time.sleep(HOLD_NS / 1e9)
            up_receipt = owner.call("up", lease, "F8")
            hold_finished_ns = time.perf_counter_ns()
            emitted = []
        elif arm == "candidate_v11":
            from input_owner_v11 import InputOwner

            owner = InputOwner(display_name)
            emitted: list[dict] = []
            backend = load_candidate_backend(owner, lease, case_id, emitted)
            backend.raw("F8", True)
            down_receipt = None
            hold_started_ns = time.perf_counter_ns()
            time.sleep(HOLD_NS / 1e9)
            backend.raw("F8", False)
            hold_finished_ns = time.perf_counter_ns()
            if len(emitted) != 1:
                raise RuntimeError(f"candidate emitted {len(emitted)} release rows")
            up_receipt = emitted[0]
        else:
            raise ValueError(f"unknown arm {arm}")

        time.sleep(0.1)
        code = d.keysym_to_keycode(XK.string_to_keysym("F8"))
        bitmap = d.query_keymap()
        terminal_f8_down = bool(bitmap[code // 8] & (1 << (code % 8)))
        owner_state = owner.call("input_state")
        owner.close()
        owner = None
        time.sleep(0.02)

        rows = []
        if event_log.exists():
            rows = [json.loads(line) for line in event_log.read_text().splitlines() if line.strip()]
        result = {
            "status": "completed",
            "case_id": case_id,
            "arm": arm,
            "source_blobs": source_blobs,
            "focus": focus,
            "requested_hold_ns": HOLD_NS,
            "sleep_envelope_ns": hold_finished_ns - hold_started_ns,
            "down_receipt": down_receipt,
            "release_receipt": up_receipt,
            "terminal_f8_down": terminal_f8_down,
            "owner_state": owner_state,
            "app_events": rows,
        }
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True))
        return result
    finally:
        if owner is not None:
            try:
                owner.close()
            except Exception:
                pass
        if d is not None:
            try:
                d.close()
            except Exception:
                pass
        if receiver is not None and receiver.poll() is None:
            receiver.terminate()
            try:
                receiver.wait(timeout=1)
            except subprocess.TimeoutExpired:
                receiver.kill()
        if xvfb.poll() is None:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=1)
            except subprocess.TimeoutExpired:
                xvfb.kill()
        xvfb_log.close()
        receiver_out.close()
        receiver_err.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--arm", choices=("baseline_v10", "candidate_v11"), required=True)
    parser.add_argument("--display-number", type=int, required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    try:
        result = run_case(args.case_id, args.arm, args.display_number, out)
    except BaseException as exc:
        out.mkdir(parents=True, exist_ok=True)
        failure = {"status": "error", "case_id": args.case_id, "arm": args.arm, "error": repr(exc), "traceback": traceback.format_exc()}
        (out / "result.json").write_text(json.dumps(failure, indent=2, sort_keys=True))
        raise
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
