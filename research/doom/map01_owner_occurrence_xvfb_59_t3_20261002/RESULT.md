# Result — actual Xvfb keymap witness construction

**Disposition: `PASS_XVFB_KEYMAP_WITNESS_CONSTRUCTION_SCOPED`.** The frozen
candidate ran once and exited 0; the independent raw-only auditor ran once and
exited 0; retries: 0. The audit passed 8/8 checks.

Across two repeated W down/up cycles, the isolated InputOwner emitted two
distinct occurrence IDs. For each ID, actual server-side `XQueryKeymap` samples
contained a full 32-byte bitmap and reported the W keycode 25 as
`false → true → false` at `pre_down`, `post_down`, and `post_up`. The matching
explicit-up bracket carried the same occurrence ID and was ordered after the
post-down sample and before post-up sampling. Owner close independently
recorded verified empty key state. The private Xvfb exited and its socket and
lock were removed.

This rung exposed a concrete integration assumption missed by T2's fake Xlib:
Python-Xlib 0.33 documents `Display.query_keymap()` as a list of 32 integers,
not `bytes`. The unmodified T2 copy therefore emitted six null `key_down`
values under real Python-Xlib. This T3 isolated copy converts only a valid
32-integer byte-range list to bytes before decoding. T2's source and raw/audit
remain unchanged.

Raw SHA-256:
`525f18279fc68f5631c6e031634f86e4a4178a585dddf80f7e8646bf91f4c502`.
Audit SHA-256:
`7504102817a2fe3e5f57672f9cee99fca2c1c6303e5450befcfba495aa1163d5`.
The source/freeze hashes are in `FREEZE.json` and `SOURCE_HASHES.json`.

## Interpretation and limits

This validates correspondence between XTEST-generated events and server-side
keymap snapshots on this private Xvfb build. It does **not** establish the
physical keyboard state, physical held-input occupancy/duration, application
receipt or useful effect, authority, latency benefit, safety, game/MAP01
control, or product behavior. Xvfb emitted non-fatal xkbcomp warnings for
unresolved XF86 keysyms; the server reported no fatal error, and the auditor
verified its cleanup.

Docker Desktop's `desktop-linux` Engine was unavailable and no shared slot was
allocated. To keep the experiment isolated without repairing shared WSL X11
permissions or contacting the active shared display, this construction used an
unprivileged user+mount namespace with private tmpfs `/tmp` and a TCP-disabled
Xvfb. No container, real GUI, game, model, physical input, application effect,
or network call was used. Issue #59's live threat-exposure and matched-control
gates remain open.
