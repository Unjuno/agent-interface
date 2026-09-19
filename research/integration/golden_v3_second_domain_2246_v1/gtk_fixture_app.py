"""GTK/X11 disposable fixture for the #2492 second-domain adapter rung."""
import argparse
import json
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--effect", type=Path, required=True)
    parser.add_argument("--events", type=Path)
    args = parser.parse_args()

    window = Gtk.Window(title="AgentInterfaceGtkFixture")
    window.set_default_size(400, 180)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    box.set_border_width(20)
    entry = Gtk.Entry()
    entry.set_placeholder_text("fixture input")
    label = Gtk.Label(label="unsaved")
    box.pack_start(entry, False, False, 0)
    box.pack_start(label, False, False, 0)
    window.add(box)

    def log_event(event_type, key=None):
        if args.events is not None:
            with args.events.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"type": event_type, "key": key}, sort_keys=True) + "\n")

    def save():
        value = entry.get_text()
        args.effect.write_text(json.dumps({"saved": True, "text": value}, sort_keys=True) + "\n", encoding="utf-8")
        label.set_text("saved:" + value)
        log_event("save")
        return False

    def key_press(_widget, event):
        key = Gdk.keyval_name(event.keyval)
        log_event("key_press", key)
        if key and key.lower() == "s" and event.state & Gdk.ModifierType.CONTROL_MASK:
            save()
            return True
        return False

    window.connect("key-press-event", key_press)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    xid = window.get_window().get_xid()
    args.meta.write_text(json.dumps({"window_id": xid, "toolkit": "gtk3"}, sort_keys=True) + "\n", encoding="utf-8")
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
