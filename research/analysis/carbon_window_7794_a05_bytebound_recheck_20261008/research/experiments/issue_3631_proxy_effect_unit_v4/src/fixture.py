#!/usr/bin/python3
"""Disposable GTK fixture with a unique, visually detectable action surface."""
import json
import os
from pathlib import Path
import signal

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk

out = Path(os.environ["ROW_DIR"])
mode = os.environ.get("EFFECT_MODE", "on")
count = 0
version = 1
events = out / "fixture-events.jsonl"
BUTTON_RECT = {"x": 176, "y": 72, "width": 120, "height": 32}


def record(kind, **fields):
    with events.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": kind, "count": count, "version": version,
                                 **fields}, sort_keys=True) + "\n")
        stream.flush()


window = Gtk.Window(title="proxy-fixture:0:1")
window.set_default_size(320, 120)
window.set_size_request(320, 120)
window.set_wmclass("Issue3631Fixture", "Issue3631Fixture")
fixed = Gtk.Fixed()
label = Gtk.Label(label="COUNT 0  VERSION 1")
button = Gtk.Button(label="INCREMENT")
button.set_name("proxy-target")
button.set_size_request(BUTTON_RECT["width"], BUTTON_RECT["height"])
fixed.put(label, 12, 20)
fixed.put(button, BUTTON_RECT["x"], BUTTON_RECT["y"])
window.add(fixed)

css = Gtk.CssProvider()
css.load_from_data(b"button#proxy-target { background-image: none; background-color: #2c6eaa; color: #ffffff; border: 0; padding: 0; }")
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                         Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def refresh():
    window.set_title(f"proxy-fixture:{count}:{version}")
    label.set_text(f"COUNT {count}  VERSION {version}")
    label.queue_draw()
    window.queue_draw()


def clicked(_button):
    global count, version
    record("click_ack", effect_mode=mode)
    if mode == "on":
        count += 1
        version += 1
        refresh()
        record("effect", value=count)


def bump(_signum, _frame):
    GLib.idle_add(bump_on_main)


def bump_on_main():
    global version
    version += 1
    refresh()
    record("external_version_change")
    return GLib.SOURCE_REMOVE


button.connect("clicked", clicked)
window.connect("destroy", Gtk.main_quit)
signal.signal(signal.SIGUSR1, bump)
window.show_all()
window.present()
while Gtk.events_pending():
    Gtk.main_iteration_do(False)
allocation = button.get_allocation()
button_rect = {"x": allocation.x, "y": allocation.y,
               "width": allocation.width, "height": allocation.height}
record("ready", pid=os.getpid(), button_rect=button_rect,
       window_size=[window.get_allocated_width(), window.get_allocated_height()])
Gtk.main()
