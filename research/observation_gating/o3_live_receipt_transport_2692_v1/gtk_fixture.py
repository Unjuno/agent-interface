"""Static GTK/X11 surfaces; this read-only allocation sends no input."""
import argparse
import json
import os
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--surface", required=True)
    p.add_argument("--meta", type=Path, required=True)
    a = p.parse_args()
    window = Gtk.Window(title="O3Transport-" + a.surface)
    window.set_default_size(420, 160)
    window.set_resizable(False)
    window.set_accept_focus(False)
    fixed = Gtk.Fixed()
    entry = Gtk.Entry()
    entry.set_can_focus(False)
    entry.set_placeholder_text("static observation fixture")
    entry.set_size_request(380, 36)
    status = Gtk.Label(label="status: unchanged")
    status.set_size_request(380, 32)
    fixed.put(entry, 16, 16)
    fixed.put(status, 16, 80)
    window.add(fixed)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    xid = window.get_window().get_xid()
    a.meta.parent.mkdir(parents=True, exist_ok=True)
    a.meta.write_text(json.dumps({
        "surface": a.surface,
        "pid": os.getpid(),
        "title": "O3Transport-" + a.surface,
        "xid": xid,
        "regions": {"entry": [16, 16, 380, 36], "status": [16, 80, 380, 32]},
    }, sort_keys=True) + "\n", encoding="utf-8")
    Gtk.main()


if __name__ == "__main__":
    main()
