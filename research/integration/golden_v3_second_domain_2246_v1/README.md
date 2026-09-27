# GTK/X11 second-domain fixture (#2492)

This disposable GTK3 fixture emits the X11 window ID and an independent save-effect receipt. It is intended to be driven by the existing X11 backend and golden-v3 contract; it does not define a new backend or grant authority.

The adapter runner must retain the source observation/binding revisions, lease, input ledger, effect receipt, and cleanup evidence. This fixture alone is not a PASS for #2492.

Run it in the pinned GTK/Xvfb container with `DISPLAY` set.