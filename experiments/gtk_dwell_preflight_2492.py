import json
import time
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, GLib

CASES = [("fast", 0.05, 0.20), ("delayed", 0.35, 0.20),
         ("absent", None, 0.20), ("late", 0.35, 0.50)]
rows = []
for name, delay, horizon in CASES:
    window = Gtk.Window(title="gtk-fixture")
    label = Gtk.Label(label="pending")
    window.add(label)
    window.show_all()
    changed = {"done": False}

    def effect(label=label, changed=changed):
        label.set_text("done")
        changed["done"] = True
        return False

    if delay is not None:
        GLib.timeout_add(round(delay * 1000), effect)
    start = time.monotonic()
    state = "UNKNOWN"
    observed_at = None
    context = GLib.MainContext.default()
    while time.monotonic() - start < horizon:
        while context.pending():
            context.iteration(False)
        if changed["done"]:
            state = "COMPLETED"
            observed_at = time.monotonic() - start
            break
        time.sleep(0.005)
    rows.append({"case": name, "effect_delay": delay, "horizon": horizon,
                 "state": state, "observed_at": observed_at,
                 "proceeded": state == "COMPLETED"})
    window.destroy()
    while context.pending():
        context.iteration(False)

result = {"rows": rows,
          "unknown_count": sum(r["state"] == "UNKNOWN" for r in rows),
          "scope": "GTK/Xvfb fixture; not production GUI evidence"}
print(json.dumps(result, indent=2))
