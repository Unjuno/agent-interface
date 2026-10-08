#!/usr/bin/env python3
"""One-shot XTEST text delivery probe for German XKB; private Xvfb only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import subprocess
import sys
import time
from pathlib import Path

from Xlib import X, XK, display
from runtime.backends.x11_v1.backend import X11Backend, X11BackendError

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = REPO_ROOT / "runtime/backends/x11_v1/backend.py"
FORMULA = "=B2*A2"


def run_bytes(argv: list[str]) -> bytes:
    return subprocess.run(argv, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def query_layout() -> dict[str, str]:
    raw = run_bytes(["setxkbmap", "-query"]).decode("utf-8", "replace")
    return {"raw": raw, "layout": next((line.split(":", 1)[1].strip()
            for line in raw.splitlines() if line.strip().startswith("layout:")), "")}


def key_map_snapshot(conn) -> dict:
    return {
        "server_xkb": run_bytes(["xkbcomp", "-xkb", os.environ["DISPLAY"], "-"]).decode("utf-8", "replace"),
        "core_keymap": run_bytes(["xmodmap", "-pke"]).decode("utf-8", "replace"),
        "modifier_map": run_bytes(["xmodmap", "-pm"]).decode("utf-8", "replace"),
    }


def symbol_levels(backend: X11Backend, name: str, character: str) -> dict:
    code = backend._keycode(name)
    levels = [backend.d.keycode_to_keysym(code, level) for level in (0, 1)]
    selected = next((level for level, value in enumerate(levels) if value == ord(character)), None)
    return {
        "character": character, "keysym_name": name, "keycode": code,
        "level0": levels[0], "level1": levels[1], "selected_level": selected,
    }


def decode_text(receiver, event) -> tuple[str | None, dict]:
    level = 1 if event.state & X.ShiftMask else 0
    keysym = receiver.keycode_to_keysym(event.detail, level)
    name = XK.keysym_to_string(keysym)
    special = {"equal": "=", "asterisk": "*", "space": " "}
    char = special.get(name)
    if char is None and isinstance(name, str) and len(name) == 1 and name.isascii():
        char = name
    modifier = name in {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"}
    return (None if modifier else char), {
        "keycode": event.detail, "state": event.state, "level": level,
        "keysym": keysym, "keysym_name": name, "decoded": None if modifier else char,
    }


def receive_formula(receiver, expected: str, timeout: float = 3.0) -> tuple[str, list[dict]]:
    chars: list[str] = []
    events: list[dict] = []
    deadline = time.monotonic() + timeout
    last_activity = time.monotonic()
    while time.monotonic() < deadline:
        if not receiver.pending_events():
            select.select([receiver.fileno()], [], [], 0.1)
        if not receiver.pending_events():
            if len(chars) >= len(expected) and time.monotonic() - last_activity >= 0.25:
                break
            continue
        event = receiver.next_event()
        if event.type != X.KeyPress:
            continue
        last_activity = time.monotonic()
        char, row = decode_text(receiver, event)
        events.append(row)
        if char is not None:
            chars.append(char)
    return "".join(chars), events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", choices=("de", "us"), required=True)
    parser.add_argument("--replicate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "allocation": "issue3668-german-xkb-text-v2",
        "replicate": args.replicate,
        "requested_layout": args.layout,
        "formula": FORMULA,
        "status": "RUNNING",
    }
    receiver = None
    backend = None
    try:
        conn = display.Display()
        receiver = display.Display()
        server_extensions = sorted(conn.list_extensions())
        result["server_extensions"] = server_extensions
        result["server_xkb_extension"] = "XKEYBOARD" in server_extensions
        result["server_xtest_extension"] = "XTEST" in server_extensions
        result["python_xlib_xkb_binding"] = conn.has_extension("XKEYBOARD")
        result["python_xlib_xtest_binding"] = conn.has_extension("XTEST")
        if not result["server_xkb_extension"] or not result["server_xtest_extension"]:
            raise RuntimeError("required server-advertised XKEYBOARD/XTEST extension missing")
        before_layout = query_layout()
        before_maps = key_map_snapshot(conn)
        result["before"] = {"layout": before_layout, "maps": before_maps}

        layout_command = None
        if args.layout == "de":
            layout_command = ["setxkbmap", "-layout", "de"]
            subprocess.run(layout_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        after_layout = query_layout()
        after_maps = key_map_snapshot(conn)
        result["layout_command"] = layout_command
        result["after"] = {"layout": after_layout, "maps": after_maps}

        screen = receiver.screen()
        receiver_window = screen.root.create_window(
            10, 10, 300, 60, 0, screen.root_depth, X.InputOutput,
            X.CopyFromParent, event_mask=X.KeyPressMask,
        )
        receiver_window.map()
        receiver.sync()
        receiver_window.set_input_focus(X.RevertToParent, X.CurrentTime)
        receiver.sync()

        backend = X11Backend(os.environ["DISPLAY"], {})
        levels = {
            "=": symbol_levels(backend, "equal", "="),
            "*": symbol_levels(backend, "asterisk", "*"),
        }
        result["symbol_levels"] = levels
        plan = backend._text_plan(FORMULA)
        result["planned_chords"] = plan

        before_preflight = backend.emissions
        receiver.sync()
        receiver_before = receiver.pending_events()
        try:
            backend.preflight({"ops": [{"op": "text", "text": FORMULA + "€"}]})
            result["unsupported_refused"] = False
        except X11BackendError as exc:
            result["unsupported_refused"] = True
            result["unsupported_error"] = str(exc)
        result["unsupported_emissions_before"] = before_preflight
        result["unsupported_emissions_after"] = backend.emissions
        result["receiver_events_before_delivery"] = receiver_before

        backend.text(FORMULA)
        backend.d.sync()
        decoded, received = receive_formula(receiver, FORMULA)
        result["decoded_formula"] = decoded
        result["received_keypresses"] = received
        result["emissions_for_formula"] = backend.emissions - before_preflight
        result["tracked_held_keys_after"] = sorted(backend.held_keycodes)
        keymap = backend.d.query_keymap()
        planned_names = {key for chord in plan for key in chord}
        keycodes = {name: backend._keycode(name) for name in sorted(planned_names)}
        result["key_state_after"] = {
            name: bool(keymap[code // 8] & (1 << (code % 8)))
            for name, code in keycodes.items()
        }
        result["backend_git_blob"] = subprocess.run(
            ["git", "hash-object", str(BACKEND_PATH)], cwd=REPO_ROOT,
            check=True, text=True, stdout=subprocess.PIPE,
        ).stdout.strip()
        result["backend_sha256"] = sha(BACKEND_PATH.read_bytes())
        result["status"] = "ROW_RECORDED"
        conn.sync()
    except Exception as exc:
        result["status"] = "STOP_OR_FAIL"
        result["error"] = repr(exc)
        if backend is not None:
            result["backend_emissions_at_error"] = backend.emissions
    finally:
        try:
            if backend is not None:
                backend.close()
        except Exception as exc:
            result["backend_close_error"] = repr(exc)
        try:
            if receiver is not None:
                receiver.close()
        except Exception as exc:
            result["receiver_close_error"] = repr(exc)
        if "conn" in locals():
            try:
                conn.close()
            except Exception:
                pass
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    rendered = json.dumps(result, sort_keys=True)
    print(rendered)
    return 0 if result["status"] == "ROW_RECORDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
