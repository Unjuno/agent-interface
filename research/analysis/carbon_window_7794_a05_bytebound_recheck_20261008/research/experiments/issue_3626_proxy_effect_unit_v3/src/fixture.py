#!/usr/bin/python3
"""Disposable GTK counter fixture. One instance belongs to one formal row."""
import json
import os
from pathlib import Path
import signal

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

out = Path(os.environ["ROW_DIR"])
mode = os.environ.get("EFFECT_MODE", "on")
count = 0
version = 1
events = out / "fixture-events.jsonl"


def record(kind, **fields):
    with events.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": kind, "count": count, "version": version, **fields}, sort_keys=True) + "\n")
        stream.flush()


window = Gtk.Window(title="proxy-fixture:0:1")
window.set_default_size(320, 120)
window.set_wmclass("Issue3610Fixture", "Issue3610Fixture")
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
box.set_border_width(12)
label = Gtk.Label(label="COUNT 0")
button = Gtk.Button(label="INCREMENT")
box.pack_start(label, True, True, 0)
box.pack_start(button, True, True, 0)
window.add(box)


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
record("ready", pid=os.getpid())
Gtk.main()
