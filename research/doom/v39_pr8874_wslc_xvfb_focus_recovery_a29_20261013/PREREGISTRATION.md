# V39 focus-target release observation and terminal cleanup A29

## H/T/D/C/U

- H: After a held backend-owned `w` loses focus from window A to window B, an explicit backend UP will be observed as a matching KeyRelease by B (the new focused client), with server keymap-up and a linked owner receipt; calling the terminal release path will verify empty owner state and clear admission cache.
- T: One offline WSLc run. Use the frozen current-workspace V39 backend and A09 current-main V4/V12 owner. Xvfb: select key events on A and B, admit one `w` down in A, focus B, observe FocusOut on A and verify focus B; issue one explicit UP; observe KeyRelease at B; query server keymap; call terminal `release_all()` and record cache count, owner records and shutdown.
- D: PASS_METHOD_SCOPED requires matching KeyPress in A and KeyRelease in B for the same keycode, observed FocusOut, confirmed focus B, keymap down before and up after, one admission-linked verified explicit-UP/XSync record, verified terminal empty release, zero admission-cache entries, stopped owner, Xvfb exit 0, removed container, source-manifest pass and independent audit pass. Any missing criterion is FAIL. Setup failure before key-down is STOP. One invocation, no retry.
- C: Xvfb/XTEST establishes only virtual X11 event delivery and keymap behavior. It cannot establish application use, production focus-monitor timing, or game/task effect.
- U: No Doom/MAP01, model wait, threat, visual policy, physical desktop, live allocation, task effect, or useful-feedback measurement.

Frozen runtime: WSLc 3.0.1.0; image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`; no network; one CPU; read-only input and separate output; UID 65534; --rm. Host cgroup/swap enforcement unavailable. Source hashes are in SOURCE_MANIFEST.json.
