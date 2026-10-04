"""One-shot same-connection Python-Xlib event-queue prefetch diagnostic."""
import json
import os
import select
import subprocess
import time

from Xlib import X, XK, display
from Xlib.ext import xtest


def key_down(connection, keycode):
    bits = connection.query_keymap()
    return bool(bits[keycode // 8] & (1 << (keycode % 8)))


def event_row(event, kind, keycode, window_id):
    """Serialize arbitrary queued events without assuming key-event fields."""
    detail = getattr(event, "detail", None)
    window = getattr(event, "window", None)
    event_window_id = getattr(window, "id", None)
    row = {"class": type(event).__name__, "type": int(event.type),
           "detail": int(detail) if isinstance(detail, int) else None,
           "window_id": int(event_window_id) if isinstance(event_window_id, int) else None}
    row["matches"] = (row["type"] == kind and row["detail"] == keycode
                      and row["window_id"] == window_id)
    return row


def collect_target(connection, kind, keycode, window_id):
    deadline = time.monotonic() + 1.0
    rows = []
    queued_snapshot = [event_row(event, kind, keycode, window_id)
                       for event in list(connection.display.event_queue)]
    queued_before_select = len(queued_snapshot)
    readable, _, _ = select.select([connection.fileno()], [], [], 0.05)
    readable_after_queue_check = bool(readable)
    while time.monotonic() < deadline:
        pending = connection.pending_events()
        while pending:
            event = connection.next_event()
            row = event_row(event, kind, keycode, window_id)
            rows.append(row)
            if row["matches"]:
                return {"queued_before_select": queued_before_select,
                        "queued_snapshot_before_select": queued_snapshot,
                        "target_prefetched_before_select": any(r["matches"] for r in queued_snapshot),
                        "socket_readable_after_queue_check": readable_after_queue_check,
                        "event_rows": rows, "matched_event": row,
                        "pending_events_after_collection": connection.pending_events()}
            pending -= 1
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        select.select([connection.fileno()], [], [], min(remaining, 0.05))
    return {"queued_before_select": queued_before_select,
            "queued_snapshot_before_select": queued_snapshot,
            "target_prefetched_before_select": any(r["matches"] for r in queued_snapshot),
            "socket_readable_after_queue_check": readable_after_queue_check,
            "event_rows": rows, "matched_event": None,
            "pending_events_after_collection": connection.pending_events()}


def main():
    xvfb_version = subprocess.run(["Xvfb", "-version"], capture_output=True,
                                  text=True)
    raw = {
        "schema": "xlib-query-keymap-prefetch-a05-v1",
        "allocation_id": "MAP01-V39-XLIB-QUERY-PREFETCH-A05-20261005-02",
        "candidate_invocations": 1, "status": "STOP",
        "environment": {"python": subprocess.run(["python3", "--version"],
            capture_output=True, text=True).stdout.strip(),
            "xvfb": (xvfb_version.stderr or xvfb_version.stdout).splitlines()[0]},
        "edges": [], "cleanup": {},
    }
    server = client = injector = window = None
    try:
        server = subprocess.Popen(["Xvfb", "-displayfd", "1", "-screen", "0",
            "320x240x24", "-nolisten", "tcp", "-ac"], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        ready, _, _ = select.select([server.stdout], [], [], 5)
        if not ready:
            raise TimeoutError("Xvfb display allocation timeout")
        number = server.stdout.readline().strip()
        if not number.isdecimal():
            raise RuntimeError("Xvfb returned an invalid display number")
        display_name = ":" + number
        client = display.Display(display_name)
        injector = display.Display(display_name)
        screen = client.screen()
        window = screen.root.create_window(10, 10, 120, 80, 0,
            screen.root_depth, X.InputOutput, X.CopyFromParent,
            event_mask=X.KeyPressMask | X.KeyReleaseMask)
        window.map()
        client.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        client.sync()
        injector.sync()
        focus = client.get_input_focus().focus
        focus_id = int(focus.id)
        keycode = int(client.keysym_to_keycode(XK.string_to_keysym("a")))
        if focus_id != int(window.id) or keycode <= 0:
            raise RuntimeError("focused client/keycode setup failed")
        while client.pending_events():
            client.next_event()
        raw["fixture"] = {"display": display_name, "window_id": int(window.id),
                           "focus_id": focus_id, "keycode": keycode}

        for label, event_type, expected_down in (("down", X.KeyPress, True),
                                                  ("up", X.KeyRelease, False)):
            started = time.perf_counter_ns()
            xtest.fake_input(injector, event_type, keycode)
            injector.sync()
            injected = time.perf_counter_ns()
            down = key_down(client, keycode)
            reply_returned = time.perf_counter_ns()
            receipt = collect_target(client, event_type, keycode, int(window.id))
            raw["edges"].append({"label": label, "expected_key_down": expected_down,
                "observed_key_down": down, "inject_started_ns": started,
                "inject_synced_ns": injected, "query_reply_returned_ns": reply_returned,
                **receipt})
            if receipt["matched_event"] is None:
                raise RuntimeError("expected client key event not observed")
        raw["candidate_complete"] = True
        raw["status"] = "CANDIDATE_COMPLETE"
    except Exception as exc:
        raw["candidate_complete"] = False
        raw["error"] = repr(exc)
        raw["status"] = "CANDIDATE_ERROR"
    finally:
        for name, connection in (("client", client), ("injector", injector)):
            if connection is not None:
                try:
                    connection.close()
                except Exception as exc:
                    raw["cleanup"][name + "_close_error"] = repr(exc)
        if server is not None:
            if server.poll() is None:
                server.terminate()
            try:
                _, stderr = server.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                _, stderr = server.communicate(timeout=3)
                raw["cleanup"]["forced_kill"] = True
            raw["cleanup"].update({"xvfb_exit": server.returncode,
                "xvfb_stopped": server.poll() is not None, "xvfb_stderr": stderr})
    print(json.dumps(raw, sort_keys=True))
    raise SystemExit(0 if raw.get("candidate_complete") is True else 1)


if __name__ == "__main__":
    main()
