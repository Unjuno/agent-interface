# A02 — Xlib query reply event-queue diagnostic

Issue #59, as a bounded diagnostic for the incomplete event receipt in per-key release A03. This does not rerun A03 or test the game/runtime.

A01 stopped before candidate because apt ran as the default unprivileged guest user. A02 keeps the hypothesis, candidate, auditor and decision rules, but runs the exact pinned dependency setup as explicit OrbStack user `root` and records `id -u`; A01 remains preserved under `predecessor/A01/`.

## H / T / D / C / U

- **H:** Under Python-Xlib 0.33 / Xvfb, if a focused client receives an XTEST key event and then calls `query_keymap()` on the same X connection, the synchronous reply parser may place the event in Xlib's in-memory event queue. Afterward the socket may have no readable bytes while `pending_events()` returns the queued event. This would explain why A03's `select(fileno)`-only wait could time out after 80 `query_keymap()` calls.
- **T:** In one fresh isolated Ubuntu 24.04 arm64 OrbStack guest, run one frozen local-Xvfb probe. For one press and one release, inject through a separate XTEST connection, synchronously call `query_keymap()` on the focused event-client connection, record the Xlib queue size before any receive poll, then test socket readiness. Drain with `pending_events()` and `next_event()` and record exact window/keycode/type and keymap state. Run the frozen raw-only auditor once only if candidate exits 0.
- **D:** PASS only if both edges are already queued before the readiness test, the socket is not readable, `pending_events()` reports each queued event, events match exact type/window/keycode, keymap changes false→true→false, and Xvfb exits 0. A complete mismatch is FAIL. Missing output or cleanup is STOP. Candidate once; no retry.
- **C:** Different X connections, XTEST routing, timing, or server scheduling may keep the event in the socket instead of the Xlib queue. In that case this probe will not establish A03's hypothesized observer bug.
- **U:** This is a Python-Xlib/Xvfb event-queue diagnostic only. It does not prove what remained queued during A03, and establishes no real OS input, per-admission release, game effect, model behavior, threat response, recovery, or MAP01 progress.

Context: A03 source in PR #7771 calls `query_keymap()` after each generated edge and later waits using `select()` without checking `pending_events()`. Current-main X11 event-routing A05 uses a separate X connection for server keymap samples and for its event sink, so that PASS is related but not direct evidence for same-connection queue prefetch. A03 raw, source and candidate/auditor outcomes remain immutable.
