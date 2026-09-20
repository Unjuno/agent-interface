#!/usr/bin/env python3
"""Small GTK window whose visible counter is changed by X11 Space presses."""
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk


mode = os.environ.get("EFFECT_MODE", "on")
count = 0
window = Gtk.Window(title="resident-fixture:0")
window.set_default_size(320, 120)
label = Gtk.Label(label="effect-count:0")
label.set_name("effect-counter")
window.add(label)


def on_key_press(_window, event):
    global count
    if event.keyval == Gdk.KEY_space and mode == "on":
        count += 1
        label.set_text(f"effect-count:{count}")
        window.set_title(f"resident-fixture:{count}")
        label.queue_draw()
    return True


window.connect("key-press-event", on_key_press)
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
