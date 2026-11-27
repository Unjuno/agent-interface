"""Read-only native state/foreground diagnostic for a disposable fixture."""
import ctypes
import hashlib
import json
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"
TARGET = "r11-state-probe-fixture"
WM_CLOSE = 0x0010
SW_SHOW = 5


def dump(path, row):
    path.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n")


def main():
    if RUN.exists():
        raise FileExistsError(f"immutable output already exists: {RUN}")
    RUN.mkdir()
    meta = RUN / "meta.json"
    events = RUN / "events.jsonl"
    effect = RUN / "effect.json"
    stdout = (RUN / "fixture.stdout.bin").open("wb")
    stderr = (RUN / "fixture.stderr.bin").open("wb")
    cmd = [sys.executable, "-m", "runtime.backends.win32_v1.fixture_app",
        "--meta", str(meta), "--effect", str(effect), "--events", str(events)]
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
        wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    original = int(user32.GetForegroundWindow() or 0)
    proc = None
    out = {"attempt_id": "win32-r11-fixture-state-readback-20261122",
        "source_main": "1b1ce38c943a5f93d94e6a9f028f5a50ceed618b",
        "input_dispatched": False, "provider_or_model": "none",
        "original_foreground": original}
    try:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=stdout, stderr=stderr)
        deadline = time.monotonic() + 10
        while not meta.exists() and proc.poll() is None and time.monotonic() < deadline:
            time.sleep(.05)
        if proc.poll() is not None or not meta.exists():
            raise RuntimeError("fixture failed to become ready")
        hwnd = int(json.loads(meta.read_text(encoding="utf-8"))["hwnd"])
        out["fixture"] = {"pid": proc.pid, "hwnd": hwnd,
            "window_valid": bool(user32.IsWindow(hwnd)),
            "visible": bool(user32.IsWindowVisible(hwnd)),
            "foreground_after_start": int(user32.GetForegroundWindow() or 0)}
        shown = bool(user32.ShowWindow(hwnd, SW_SHOW))
        activation_return = bool(user32.SetForegroundWindow(hwnd))
        time.sleep(.15)
        foreground_after_activation = int(user32.GetForegroundWindow() or 0)
        out["activation"] = {"show_window_previous_visibility": shown,
            "set_foreground_return": activation_return,
            "foreground_after_activation": foreground_after_activation,
            "foreground_is_fixture": foreground_after_activation == hwnd}
        from runtime.backends.win32_v1.backend import Win32Backend, virtual_key
        backend = Win32Backend({TARGET: hwnd})
        try:
            out["witness_before_state_read"] = backend._async_key_state_query_witness(TARGET)
            state = backend._key_down_state(virtual_key("SHIFT"), TARGET)
            out["shift_down"] = state
            out["state_query_witness"] = list(backend._last_state_query_witness)
            out["witness_after_state_read"] = backend._async_key_state_query_witness(TARGET)
            out["target_generation"] = backend.target_generation(TARGET)
        finally:
            backend.close()
        out["effect_file_present"] = effect.exists()
        out["fixture_events"] = [json.loads(x) for x in events.read_text(
            encoding="utf-8").splitlines()]
        out["classification"] = "PASS_STATE_READBACK_SETUP" if (
            foreground_after_activation == hwnd and state is False
            and bool(out["state_query_witness"]) and not effect.exists()
            and out["fixture_events"] == [{"hwnd": hwnd, "kind": "ready"}]
        ) else "HOLD_STATE_READBACK_UNKNOWN"
    except BaseException as exc:
        out["classification"] = "HOLD_STATE_READBACK_UNKNOWN"
        out["error_type"] = type(exc).__name__
        out["error"] = str(exc)[:512]
    finally:
        if proc is not None and proc.poll() is None:
            try:
                hwnd = int(json.loads(meta.read_text(encoding="utf-8"))["hwnd"])
                user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                proc.wait(timeout=5)
            except Exception as exc:
                out["close_error"] = repr(exc)
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
        out["fixture_exit_code"] = None if proc is None else proc.poll()
        if original and user32.IsWindow(original):
            out["restore_foreground_return"] = bool(user32.SetForegroundWindow(original))
        time.sleep(.1)
        out["foreground_after_restore"] = int(user32.GetForegroundWindow() or 0)
        out["cleanup_pass"] = out["fixture_exit_code"] == 0 and (
            not original or out["foreground_after_restore"] == original)
        dump(RUN / "probe.json", out)
        stdout.close()
        stderr.close()
    print(json.dumps(out, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

