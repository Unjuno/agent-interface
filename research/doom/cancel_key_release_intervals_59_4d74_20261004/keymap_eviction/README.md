# Key-up after keysym removal

This follow-up tests a keymap change that removes the logical key entirely. The
pushed candidate already stored the admission-time keycode, but it looked up
the current keysym before consulting that record. If W had been admitted at
code 87 and W later resolved to code 0, `up(W)` raised `ValueError` and left 87
held until later cleanup.

Key-up now uses the stored `(lease, logical key)` admission directly and does
not consult the current symbol map. Only key-down resolves a keysym. The exact
pre-fix source fails with code 87 still down and no explicit-up receipt; the
candidate releases code 87 and records that exact admission-time identity.

Run `python3 -B -m research.doom.cancel_key_release_intervals_59_4d74_20261004.keymap_eviction.audit`
to verify source pins, retained outputs, and the 24-test ordered adjacent
suite. This is a fake-Xlib construction test, not a live allocation.
