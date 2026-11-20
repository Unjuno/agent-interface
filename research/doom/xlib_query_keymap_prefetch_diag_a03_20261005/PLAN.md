# A03 — Xlib query reply event-queue diagnostic

Issue #59, as a bounded observer diagnostic after per-key release A03 (PR #7771) produced an incomplete client-event receipt. This does not rerun that candidate or test the game/runtime.

A01 stopped before dependency setup because apt ran as the default unprivileged guest user. A02 stopped before dependency setup because `orb run -u root` changed HOME to `/root` while the extracted bundle remained under `/home/taka`. Both outcomes are retained under `predecessor/`; candidate/auditor invocation counts for both are 0/0. A03 uses a new guest, selects `/home/taka/xlib-query-prefetch-a03` explicitly with OrbStack `--workdir` for root setup, and checks UID 0 before apt.

## H / T / D / C / U

- **H:** Under Python-Xlib 0.33 / Xvfb, if a focused client receives an XTEST key event and then calls `query_keymap()` on the same X connection, the synchronous reply parser may place the event in Xlib's in-memory event queue. Afterward the socket may have no readable bytes while `pending_events()` returns the queued event. This could explain A03's `select(fileno)`-only timeout after 80 keymap queries.
- **T:** In one fresh isolated Ubuntu 24.04 arm64 OrbStack guest, run one frozen local-Xvfb probe. For one press and one release, inject through a separate XTEST connection, synchronously call `query_keymap()` on the focused event-client connection, record the Xlib queue size before any receive poll, test socket readiness, then drain with `pending_events()` / `next_event()` and record exact window/keycode/type and keymap state. Run the frozen raw-only auditor once only if candidate exits 0.
- **D:** PASS only if both edges are already queued before the readiness test, the socket is not readable, `pending_events()` reports each queued event, events match exact type/window/keycode, keymap changes false→true→false, and Xvfb exits 0. A complete mismatch is FAIL. Missing output or cleanup is STOP. Candidate once; no retry.
- **C:** Different X connections, XTEST routing, timing, or server scheduling may keep the event in the socket instead of the Xlib queue. In that case this probe will not establish A03's hypothesized observer bug.
- **U:** This is a Python-Xlib/Xvfb event-queue diagnostic only. Even a PASS cannot prove what remained queued during A03. No real OS input, per-admission physical release, game effect, model behavior, threat response, recovery, or MAP01 progress is established.

Current-main X11 routing A05 uses separate server-sampling and event-client connections, so its routing PASS is related but does not answer this same-connection question. A03 raw/source and both setup STOPs remain unchanged.
