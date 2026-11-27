"""One-shot Win32 fixture state-readback probe; waits for Computer Use activation."""
import ctypes
import json
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
TARGET = "r12-cua-state-probe-fixture"
WM_CLOSE = 0x0010


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n")


def run():
    if RUN.exists():
        raise FileExistsError(f"immutable output already exists: {RUN}")
    RUN.mkdir()
    meta, effect, events = (RUN / name for name in ("meta.json", "effect.json", "events.jsonl"))
    activate_receipt = RUN / "computer-use-activation.json"
    stdout = (RUN / "fixture.stdout.bin").open("wb")
    stderr = (RUN / "fixture.stderr.bin").open("wb")
    command = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
        "--meta", str(meta), "--effect", str(effect), "--events", str(events)]
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
        wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    original = int(user32.GetForegroundWindow() or 0)
    process = None
    out = {"attempt_id": "win32-r12-cua-foreground-state-readback-20261122",
        "source_main": "1b1ce38c943a5f93d94e6a9f028f5a50ceed618b",
        "input_dispatched": False, "provider_or_model": "none",
        "original_foreground": original}
    try:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        ready_by = time.monotonic() + 10
        while not meta.exists() and process.poll() is None and time.monotonic() < ready_by:
            time.sleep(.05)
        if process.poll() is not None or not meta.exists():
            raise RuntimeError("fixture did not become ready")
        hwnd = int(json.loads(meta.read_text(encoding="utf-8"))["hwnd"])
        out["fixture"] = {"pid": process.pid, "hwnd": hwnd,
            "window_valid": bool(user32.IsWindow(hwnd)),
            "foreground_before_cua": int(user32.GetForegroundWindow() or 0)}
        save(RUN / "ready.json", out)
        activation_deadline = time.monotonic() + 60
        while not activate_receipt.exists() and time.monotonic() < activation_deadline:
            if process.poll() is not None:
                raise RuntimeError("fixture exited before Computer Use activation")
            time.sleep(.05)
        if not activate_receipt.exists():
            out["classification"] = "HOLD_COMPUTER_USE_ACTIVATION_TIMEOUT"
            raise RuntimeError("Computer Use activation receipt not supplied before timeout")
        activation = json.loads(activate_receipt.read_text(encoding="utf-8"))
        out["computer_use_activation"] = activation
        foreground = int(user32.GetForegroundWindow() or 0)
        out["foreground_after_cua"] = foreground
        out["foreground_matches_fixture"] = foreground == hwnd
        from runtime.backends.win32_v1.backend import Win32Backend, virtual_key
        backend = Win32Backend({TARGET: hwnd})
        try:
            out["witness_before_state"] = backend._async_key_state_query_witness(TARGET)
            state = backend._key_down_state(virtual_key("SHIFT"), TARGET)
            out["shift_down"] = state
            out["state_query_witness"] = list(backend._last_state_query_witness)
            out["witness_after_state"] = backend._async_key_state_query_witness(TARGET)
            out["target_generation"] = backend.target_generation(TARGET)
        finally:
            backend.close()
        out["effect_file_present"] = effect.exists()
        out["fixture_events"] = [json.loads(row) for row in events.read_text(
            encoding="utf-8").splitlines()]
        out["classification"] = "PASS_STATE_READBACK_SETUP" if (
            activation.get("fixture_window_id") == hwnd
            and activation.get("activate_call_returned") is True
            and out["foreground_matches_fixture"] is True
            and state is False and bool(out["state_query_witness"])
            and not effect.exists()
            and out["fixture_events"] == [{"hwnd": hwnd, "kind": "ready"}]
        ) else "HOLD_STATE_READBACK_UNKNOWN"
    except BaseException as exc:
        if out.get("classification") != "HOLD_COMPUTER_USE_ACTIVATION_TIMEOUT":
            out["classification"] = "HOLD_STATE_READBACK_UNKNOWN"
        out["error_type"] = type(exc).__name__
        out["error"] = str(exc)[:512]
    finally:
        if process is not None and process.poll() is None:
            try:
                hwnd = int(json.loads(meta.read_text(encoding="utf-8"))["hwnd"])
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                process.wait(timeout=5)
            except Exception as exc:
                out["close_error"] = repr(exc)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except Exception:
                    pass
        out["fixture_exit_code"] = None if process is None else process.poll()
        if original and user32.IsWindow(original):
            out["restore_foreground_return"] = bool(user32.SetForegroundWindow(original))
        time.sleep(.1)
        out["foreground_after_restore"] = int(user32.GetForegroundWindow() or 0)
        out["cleanup_pass"] = out["fixture_exit_code"] == 0 and (
            not original or out["foreground_after_restore"] == original)
        save(RUN / "probe.json", out)
        stdout.close()
        stderr.close()
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()

