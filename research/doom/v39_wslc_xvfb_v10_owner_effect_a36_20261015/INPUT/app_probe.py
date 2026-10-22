"""Separate synthetic X11 app; app events go to a dedicated JSONL file."""
import argparse
import json
import select
import sys
import time

from Xlib import X, Xatom, XK, display


def emit(stream, row):
    stream.write(json.dumps(row, sort_keys=True) + "\n")
    stream.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--display", required=True)
    parser.add_argument("--log", required=True)
    args = parser.parse_args()

    with open(args.log, "a", encoding="utf-8", buffering=1) as events:
        connection = display.Display(args.display)
        screen = connection.screen()
        root = screen.root
        window = root.create_window(
            20, 20, 320, 200, 0, screen.root_depth,
            X.InputOutput, X.CopyFromParent,
            event_mask=X.KeyPressMask | X.KeyReleaseMask)
        counter_atom = connection.intern_atom("_A36_TASK_COUNTER")
        window.change_property(counter_atom, Xatom.CARDINAL, 32, [0])
        window.map()
        connection.sync()
        connection.set_input_focus(window, X.RevertToParent, X.CurrentTime)
        connection.sync()
        keycode = int(connection.keysym_to_keycode(XK.string_to_keysym("a")))
        if keycode <= 0:
            raise RuntimeError("a key has no X11 keycode")
        focus = connection.get_input_focus().focus
        focus_id = focus.id if hasattr(focus, "id") else int(focus)
        emit(events, {"event": "app_ready", "window_id": int(window.id),
                      "counter_atom": int(counter_atom), "initial_counter": 0,
                      "focus_id": int(focus_id), "keycode": keycode,
                      "ready_ns": time.perf_counter_ns()})

        task_count = 0
        while True:
            readable, _, _ = select.select(
                [connection.fileno(), sys.stdin.fileno()], [], [], 1.0)
            if sys.stdin.fileno() in readable:
                if sys.stdin.readline().strip() == "STOP":
                    break
            if connection.fileno() not in readable:
                continue
            while connection.pending_events():
                event = connection.next_event()
                if event.type == X.KeyPress and event.detail == keycode:
                    before = task_count
                    task_count = 1
                    window.change_property(counter_atom, Xatom.CARDINAL, 32,
                                           [task_count])
                    connection.sync()
                    emit(events, {"event": "app_keypress_effect",
                                  "type": int(event.type),
                                  "keycode": int(event.detail),
                                  "window_id": int(event.window.id),
                                  "counter_before": before,
                                  "counter_after": task_count,
                                  "effect_ns": time.perf_counter_ns()})
                elif event.type == X.KeyRelease and event.detail == keycode:
                    emit(events, {"event": "app_keyrelease",
                                  "type": int(event.type),
                                  "keycode": int(event.detail),
                                  "window_id": int(event.window.id),
                                  "release_ns": time.perf_counter_ns()})

        connection.close()
        emit(events, {"event": "app_stopped", "counter": task_count,
                      "stopped_ns": time.perf_counter_ns()})


if __name__ == "__main__":
    main()
