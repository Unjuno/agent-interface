"""Deliver one real XTest Ctrl+S sequence to the disposable Tk construction fixture."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from Xlib import X, XK, display
from Xlib.ext import xtest

from audit import audit_row
from fixture import __file__ as fixture_module


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def wait_for(path: Path, process: subprocess.Popen[bytes], timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        if process.poll() is not None:
            raise RuntimeError(f"fixture exited before readiness: {process.returncode}")
        time.sleep(0.02)
    raise TimeoutError(f"fixture did not produce {path.name}")


def fake_key(d: display.Display, keysym_name: str) -> int:
    keysym = XK.string_to_keysym(keysym_name)
    if not keysym:
        raise ValueError(f"unknown keysym: {keysym_name}")
    keycode = d.keysym_to_keycode(keysym)
    if not keycode:
        raise ValueError(f"no X keycode for keysym: {keysym_name}")
    xtest.fake_input(d, X.KeyPress, detail=keycode)
    d.sync()
    time.sleep(0.01)
    xtest.fake_input(d, X.KeyRelease, detail=keycode)
    d.sync()
    time.sleep(0.01)
    return keycode


def make_manifest(root: Path) -> dict[str, object]:
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"):
        data = path.read_bytes()
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = {"schema": "issue-3628/xtest-construction-manifest-v1", "files": rows}
    write_json(root / "manifest.json", manifest)
    return manifest


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe_xtest.py OUTPUT_DIR (must not already exist)")
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=False)
    meta = out / "fixture-meta.json"
    effect = out / "fixture-effect.jsonl"
    events = out / "fixture-events.jsonl"
    fixture_log_path = out / "fixture.log"
    fixture_path = Path(fixture_module).resolve()
    proc: subprocess.Popen[bytes] | None = None
    d: display.Display | None = None
    error: str | None = None
    fixture_signal: int | None = None
    effect_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    audit: dict[str, object] | None = None
    keycodes: dict[str, int] = {}
    marker = "m3628test"
    fixture_log = fixture_log_path.open("wb")

    try:
        proc = subprocess.Popen(
            [sys.executable, str(fixture_path), "--meta", str(meta), "--effect", str(effect), "--events", str(events)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=fixture_log,
        )
        wait_for(meta, proc)
        fixture_meta = json.loads(meta.read_text(encoding="utf-8"))
        d = display.Display()
        if not d.has_extension("XTEST"):
            raise RuntimeError("X server does not expose XTEST")

        window = d.create_resource_object("window", int(fixture_meta["window_id"]))
        root_window = d.screen().root
        # Focus is an explicit prerequisite; this probe deliberately does not
        # infer targetability from a successful request to an unmapped child.
        window.map()
        d.sync()
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        d.sync()
        input_focus = d.get_input_focus().focus
        if input_focus.id != window.id:
            raise RuntimeError(f"fixture did not own X input focus: {input_focus.id}")
        # The fixture uses fixed +80+90 geometry and a 400x180 client area.
        xtest.fake_input(d, X.MotionNotify, root=root_window.id, x=150, y=145)
        xtest.fake_input(d, X.ButtonPress, detail=1)
        d.sync()
        time.sleep(0.03)
        xtest.fake_input(d, X.ButtonRelease, detail=1)
        d.sync()
        time.sleep(0.05)
        pointer = root_window.query_pointer()
        keycodes["pointer_x"] = pointer.root_x
        keycodes["pointer_y"] = pointer.root_y

        for char in marker:
            keycodes[char] = fake_key(d, char)

        control = d.keysym_to_keycode(XK.string_to_keysym("Control_L"))
        letter_s = d.keysym_to_keycode(XK.string_to_keysym("s"))
        if not control or not letter_s:
            raise RuntimeError("Ctrl+S keycodes are unavailable")
        keycodes["Control_L"] = control
        keycodes["save_s"] = letter_s
        xtest.fake_input(d, X.KeyPress, detail=control)
        d.sync()
        time.sleep(0.03)
        xtest.fake_input(d, X.KeyPress, detail=letter_s)
        d.sync()
        time.sleep(0.03)
        xtest.fake_input(d, X.KeyRelease, detail=letter_s)
        d.sync()
        time.sleep(0.02)
        xtest.fake_input(d, X.KeyRelease, detail=control)
        d.sync()
        wait_for(effect, proc)
        time.sleep(0.05)

        effect_rows = [json.loads(line) for line in effect.read_text(encoding="utf-8").splitlines()]
        event_rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
        audit = audit_row(event_rows, effect_rows, marker)
        if not audit["pass"]:
            raise AssertionError(f"independent event/effect audit failed: {audit}")
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if d is not None:
            d.close()
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
            fixture_signal = proc.returncode
        fixture_log.close()

    result = {
        "schema": "issue-3628/xtest-construction-result-v1",
        "mode": "construction-only-real-x11-xtest",
        "marker": marker,
        "fixture_source_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "keycodes": keycodes,
        "event_count": len(event_rows),
        "effect_receipt_count": len(effect_rows),
        "audit": audit,
        "fixture_exit_code": None if proc is None else proc.returncode,
        "fixture_terminated_by_probe": fixture_signal == -15,
        "fixture_reaped": proc is None or proc.poll() is not None,
        "error": error,
    }
    write_json(out / "probe-result.json", result)
    make_manifest(out)
    print(json.dumps(result, sort_keys=True))
    if error is not None or not result["fixture_reaped"]:
        raise SystemExit(error or "fixture process was not reaped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
