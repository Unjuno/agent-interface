#!/usr/bin/env python3
"""One-shot X11 coordinate-frame study for Issue #4439.

This runner contains a private Xlib fixture and three frozen capture policies.
It has no GUI input emission and writes each completed case immediately.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
import secrets
import socket
import struct
import subprocess
import tempfile
import time
from pathlib import Path

from Xlib import X, display

W, H = 120, 80
START = (20, 20)
MOVED = (220, 160)
POLICIES = ("PINNED_SCREEN", "REFRESH_SCREEN", "WINDOW_CLIENT")
SCHEDULES = ("STABLE", "MOVE_BEFORE", "MOVE_BETWEEN")
REPS = (0, 1, 2)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":")).encode()


def packed(data):
    z = gzip.compress(data, compresslevel=9, mtime=0)
    return {"encoding": "base64+gzip", "bytes": len(data), "sha256": sha(data), "gzip_sha256": sha(z), "data": base64.b64encode(z).decode("ascii")}


def xauthority(path, display_no):
    cookie = secrets.token_bytes(16)
    addr = socket.gethostname().encode()
    number = str(display_no).encode()
    name = b"MIT-MAGIC-COOKIE-1"
    rec = struct.pack(">H", 256)
    for item in (addr, number, name, cookie):
        rec += struct.pack(">H", len(item)) + item
    Path(path).write_bytes(rec)
    os.chmod(path, 0o600)
    return cookie


def wait_x(display_no, auth_path, timeout=5.0):
    env = dict(os.environ, DISPLAY=f":{display_no}", XAUTHORITY=str(auth_path))
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        record = None
        try:
            d = display.Display(env["DISPLAY"])
            d.close()
            return env
        except Exception:
            time.sleep(.025)
    raise TimeoutError("Xvfb did not accept authenticated local connection")


def target_pattern(win, d):
    for y in range(H):
        r = (37 + y * 3) & 255
        g = (71 + y * 5) & 255
        b = (113 + y * 7) & 255
        gc = win.create_gc(foreground=(r << 16) | (g << 8) | b)
        win.fill_rectangle(gc, 0, y, W, 1)
        gc.free()
    d.sync()


def image_bytes(obj):
    v = obj.data
    return v.encode("latin1") if isinstance(v, str) else bytes(v)


def capture(root_or_window, x, y):
    img = root_or_window.get_image(x, y, W, H, X.ZPixmap, 0xFFFFFFFF)
    if img is None:
        raise RuntimeError("XGetImage returned None")
    return image_bytes(img)


def run_case(case_id, policy, schedule, repetition):
    # Use a distinct display number per serial case; Xvfb TCP is disabled and
    # the server accepts only the one temporary MIT-MAGIC-COOKIE authority.
    display_no = 80 + case_id
    with tempfile.TemporaryDirectory(prefix=f"x11-4439-{case_id}-") as td:
        auth = Path(td) / "Xauthority"
        xauthority(auth, display_no)
        xvfb = subprocess.Popen(["Xvfb", f":{display_no}", "-screen", "0", "400x300x24", "-nolisten", "tcp", "-auth", str(auth)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            env = wait_x(display_no, auth)
            old_env = os.environ.copy()
            os.environ.update(env)
            try:
                d = display.Display(env["DISPLAY"])
                root = d.screen().root
                win = root.create_window(START[0], START[1], W, H, 0,
                    d.screen().root_depth, X.InputOutput, X.CopyFromParent,
                    background_pixel=0x000000, override_redirect=1,
                    event_mask=X.StructureNotifyMask)
                target_pattern(win, d)
                win.map(); d.sync()
                initial = win.get_geometry()
                initial_xy = [int(initial.x), int(initial.y)]
                initial_pixels = capture(win, 0, 0)
                if schedule == "MOVE_BEFORE":
                    win.configure(x=MOVED[0], y=MOVED[1]); d.sync()

                if policy == "PINNED_SCREEN":
                    candidate_xy = START
                elif policy == "REFRESH_SCREEN":
                    g = win.get_geometry()
                    candidate_xy = (int(g.x), int(g.y))
                else:
                    candidate_xy = None

                if schedule == "MOVE_BETWEEN":
                    # Directed check/use gap after root-coordinate resolution.
                    win.configure(x=MOVED[0], y=MOVED[1]); d.sync()

                t0 = time.monotonic_ns()
                if policy == "WINDOW_CLIENT":
                    candidate = capture(win, 0, 0)
                else:
                    candidate = capture(root, candidate_xy[0], candidate_xy[1])
                t1 = time.monotonic_ns()
                # Scoring-only oracle: bytes read from the target XID, not
                # passed into any policy above.
                oracle = capture(win, 0, 0)
                final = win.get_geometry()
                final_xy = [int(final.x), int(final.y)]
                d.close()
            finally:
                os.environ.clear(); os.environ.update(old_env)
            record = {
                "case_id": case_id, "policy": policy, "schedule": schedule,
                "repetition": repetition, "display": display_no,
                "initial_xy": initial_xy, "candidate_xy": list(candidate_xy) if candidate_xy else None,
                "final_xy": final_xy, "initial_target_sha256": sha(initial_pixels),
                "candidate_sha256": sha(candidate), "oracle_sha256": sha(oracle),
                "candidate_matches_oracle": candidate == oracle,
                "candidate_capture_ns": [t0, t1],
                "candidate_bytes": packed(candidate), "oracle_bytes": packed(oracle),
                "xvfb_pid": xvfb.pid,
                "authority_file_mode": oct(auth.stat().st_mode & 0o777),
            }
        finally:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=2)
            except subprocess.TimeoutExpired:
                xvfb.kill(); xvfb.wait(timeout=2)
            if record is not None:
                record["xvfb_returncode"] = xvfb.returncode
        if record is None:
            raise RuntimeError("case did not produce a complete record")
        return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("construction", "formal"), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    schedule = [(p, s, r) for r in REPS for s in SCHEDULES for p in POLICIES]
    if args.mode == "construction":
        schedule = [(p, s, 0) for p in POLICIES for s in SCHEDULES]
    with (out / "raw.jsonl").open("xb") as f:
        for i, (p, s, rep) in enumerate(schedule):
            row = run_case(i, p, s, rep)
            f.write(canon(row) + b"\n"); f.flush(); os.fsync(f.fileno())
    print(json.dumps({"mode": args.mode, "rows": len(schedule), "raw_sha256": sha((out / "raw.jsonl").read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
