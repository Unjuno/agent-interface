# A10 simultaneous two-key recovery

A09 passed the single-key scoped process-recovery gate. A10 tests the next specific residual: simultaneous holds of two RPC-allowlisted keys (`a` and `d`) through the same actual opt-in V15 release-batch backend, then session-only SIGKILL. It requires independent KeyPress/keymap-down for both codes before kill, KeyRelease/keymap-up for both afterward, a matching fsynced recovery receipt whose release attempts cover both keycodes, stopped owner thread, service exit 0 without force kill, and supervisor-requested clean Xvfb exit (0 or -15).

This is a new allocation with one candidate invocation and no retries. It uses a fresh absent output leaf, private Xvfb and the A09 durable event observation. No game, model, physical input, or product-level claim.
