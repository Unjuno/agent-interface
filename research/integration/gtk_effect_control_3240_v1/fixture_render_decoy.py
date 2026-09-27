"""Render a saved-looking GTK window without changing the target app state."""
import argparse
import json
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", type=Path, required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()
    window = Gtk.Window(title="AgentInterfaceGtkFixture")
    window.set_default_size(400, 180)
    label = Gtk.Label(label="saved:" + args.text)
    label.set_margin_top(70)
    window.add(label)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    args.meta.write_text(json.dumps({
        "window_id": window.get_window().get_xid(),
        "toolkit": "gtk3",
        "render_only": True,
    }, sort_keys=True) + "\n", encoding="utf-8")
    Gtk.main()


if __name__ == "__main__":
    main()
