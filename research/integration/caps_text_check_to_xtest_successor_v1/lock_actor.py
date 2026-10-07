"""Separate X11 client that changes Caps Lock at an explicit local IPC gate."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import socket
import sys
import time

from Xlib import X, display


def lock_state(display_name: str, enabled: bool) -> tuple[int, int]:
    """Set Caps Lock via a separate Xlib connection and independently observe it."""
    lib = ctypes.CDLL("libX11.so.6")
    lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
    lib.XOpenDisplay.restype = ctypes.c_void_p
    lib.XkbLockModifiers.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                     ctypes.c_uint, ctypes.c_uint]
    lib.XkbLockModifiers.restype = ctypes.c_int
    lib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
    conn = lib.XOpenDisplay(display_name.encode())
    if not conn:
        raise RuntimeError("XOpenDisplay failed")
    try:
        accepted = lib.XkbLockModifiers(
            conn, 0x100, X.LockMask, X.LockMask if enabled else 0
        )
        lib.XSync(conn, 0)
        observer = display.Display(display_name)
        try:
            mask = observer.screen().root.query_pointer().mask
        finally:
            observer.close()
        return int(accepted), int(bool(mask & X.LockMask))
    finally:
        lib.XCloseDisplay(conn)


def main() -> int:
    socket_path = Path(sys.argv[1])
    display_name = sys.argv[2]
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        server.listen(1)
        conn, _ = server.accept()
        with conn:
            raw = bytearray()
            while not raw.endswith(b"\n") and len(raw) <= 4096:
                chunk = conn.recv(1)
                if not chunk:
                    raise RuntimeError("barrier client closed before request")
                raw.extend(chunk)
            request = raw.decode("ascii").strip()
            if request != "LOCK_ON:0":
                raise ValueError("unexpected barrier request")
            candidate_sample = int(request.split(":", 1)[1])
            received_ns = time.monotonic_ns()
            pre = display.Display(display_name)
            try:
                pre_lock = int(bool(pre.screen().root.query_pointer().mask & X.LockMask))
            finally:
                pre.close()
            mutation_started_ns = time.monotonic_ns()
            accepted, post_lock = lock_state(display_name, True)
            mutation_sync_ns = time.monotonic_ns()
            if accepted != 1 or pre_lock != 0 or post_lock != 1:
                raise RuntimeError("LockMask transition did not reconcile")
            payload = {
                "request": request,
                "candidate_sample": candidate_sample,
                "actor_pid": os.getpid(),
                "received_ns": received_ns,
                "pre_lock": pre_lock,
                "mutation_started_ns": mutation_started_ns,
                "mutation_sync_ns": mutation_sync_ns,
                "accepted": accepted,
                "post_lock": post_lock,
                "ack_ns": time.monotonic_ns(),
            }
            conn.sendall(b"ACK:" + json.dumps(payload, sort_keys=True).encode() + b"\n")
            print(json.dumps(payload, sort_keys=True), flush=True)
        return 0
    finally:
        server.close()
        socket_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
