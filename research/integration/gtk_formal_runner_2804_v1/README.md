# GTK formal runner successor (#2804)

The runner now selects `/usr/bin/python3` for the GTK fixture when present.
This is required because the image's `gi` package is installed for the Debian
Python, while `PYTHONPATH=/workspace` makes the default `/usr/local/bin/python3`
unable to import it. The original source-bundle result remains unchanged; its
manifest is updated only to record this successor runner fix.

The bounded Docker allocation reached all eight cases, but the X11 adapter
returned `backend_unavailable` because the image lacks the Python `Xlib`
dependency. This is a HOLD, not formal #2606 acceptance.

