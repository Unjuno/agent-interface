"""Saved-looking GTK decoy on a distinct XID/PID; performs no input/effect."""
import argparse
import json
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", type=Path, required=True)
    args = parser.parse_args()
    window = Gtk.Window(title="AgentInterfaceGtkFixture")
    window.set_default_size(400, 180)
    window.move(450, 20)
    label = Gtk.Label(label="saved:gtk3240")
    label.set_margin_top(70)
    window.add(label)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    args.meta.write_text(json.dumps({"window_id": window.get_window().get_xid(),
                                     "title": window.get_title(),
                                     "pid": __import__("os").getpid(),
                                     "x": 450, "y": 20,
                                     "width": 400, "height": 180}) + "\n")
    Gtk.main()


if __name__ == "__main__":
    main()
