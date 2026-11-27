# V39 X11 focus-loss recovery A28

## H/T/D/C/U

- H: When the focused X11 client loses focus while one backend-owned `w` key is held, detecting `FocusOut` and issuing one backend raw-UP will produce a matching `KeyRelease` and server keymap-up within 2 seconds; terminal release will verify empty state and clear the admission cache.
- T: One offline WSLc run using the exact A27 frozen current-workspace backend and A09 current-main V4/V12 owner. Start private Xvfb, focus observer window A, admit one `w` down, verify KeyPress/keymap-down; transfer focus to window B; await FocusOut on A; issue one explicit backend raw-UP; observe KeyRelease and keymap-up; record monotonic boundaries, owner receipts, terminal cleanup, and container cleanup.
- D: PASS_METHOD_SCOPED requires FocusOut, matching KeyPress/KeyRelease, keymap down then up, FocusOut-to-observed-KeyRelease <=2 s, explicit UP receipt with identity-bound admission, verified terminal empty state/cache cleared, owner stopped, Xvfb exit 0, and independent audit pass. Missing transitions or mismatched key is FAIL. Setup failure before key-down is STOP; no retry.
- C: Xvfb/XTEST models X11 focus and server key state. FocusOut is only the controller's invalidation trigger; release is explicitly issued by the backend. This does not prove production focus monitor scheduling or Doom behavior.
- U: No game/MAP01, task effect, threat exposure, model latency, visual policy, physical desktop, live/formal allocation, or independent useful-feedback measurement.

Frozen runtime: WSLc 3.0.1.0, image sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592, offline, one CPU, read-only sources, separate writable output, UID 65534, --rm. Host memory/cgroup enforcement is not assumed. The exact source manifest is adjacent. One invocation only.
