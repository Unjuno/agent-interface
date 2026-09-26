"""Minimal GTK3 task-effect fixture for the held-out #2107 decision route."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk


def append(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=("before", "after", "none"), required=True)
    parser.add_argument("--delay-ms", type=int, required=True)
    parser.add_argument("--effect-after-press-ms", type=int, default=0)
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--effect", type=Path, required=True)
    args = parser.parse_args()
    state = {"done": False, "closed": False}

    window = Gtk.Window(title="AgentInterfaceReleaseDecision")
    window.set_decorated(False)
    window.set_default_size(400, 180)
    window.set_resizable(False)
    pending = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 400, 180)
    pending.fill(0xC71F19FF)
    done = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 400, 180)
    done.fill(0x14B833FF)
    image = Gtk.Image.new_from_pixbuf(pending)
    image.set_size_request(400, 180)
    window.add(image)

    def emit(kind: str, **extra) -> None:
        append(args.events, {"kind": kind, "at_ns": time.perf_counter_ns(), **extra})

    def finish_effect():
        if state["closed"]:
            return False
        if state["done"]:
            emit("duplicate_effect_ignored", scenario=args.scenario)
            return False
        state["done"] = True
        image.set_from_pixbuf(done)
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        row = {"effect": "DONE", "at_ns": time.perf_counter_ns(),
               "source": "gtk_fixture_key_action", "scenario": args.scenario,
               "effect_representation": "GdkPixbuf replacement"}
        args.effect.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")
        emit("effect_state_changed", scenario=args.scenario)
        return False

    def on_key(_widget, event, event_name: str):
        key = Gdk.keyval_name(event.keyval)
        if key == "F8":
            emit(event_name, key=key, hardware_keycode=int(event.hardware_keycode))
            if event_name == "key_press" and args.scenario == "before":
                GLib.timeout_add(args.effect_after_press_ms, finish_effect)
            elif event_name == "key_release" and args.scenario == "after":
                GLib.timeout_add(args.delay_ms, finish_effect)
            return True
        return False

    window.connect("key-press-event", lambda w, e: on_key(w, e, "key_press"))
    window.connect("key-release-event", lambda w, e: on_key(w, e, "key_release"))
    window.connect("destroy", lambda *_: (state.update(closed=True), Gtk.main_quit()))
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    xid = int(window.get_window().get_xid())
    canvas_xid = int(image.get_window().get_xid())
    args.meta.write_text(json.dumps({"window_id": xid, "canvas_window_id": canvas_xid,
                                     "canvas_width": image.get_allocated_width(),
                                     "canvas_height": image.get_allocated_height(),
                                     "pid": __import__("os").getpid(),
                                     "title": "AgentInterfaceReleaseDecision",
                                     "toolkit": "GTK3", "scenario": args.scenario},
                                    sort_keys=True) + "\n", encoding="utf-8")
    Gtk.main()


if __name__ == "__main__":
    main()
