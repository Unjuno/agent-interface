# A04 predeclared protocol

- H: In an isolated Ubuntu arm64 Xvfb fixture, a synchronous Python-Xlib `query_keymap()` after an injected key edge will receive/queue the matching client event; immediately after internal-queue inspection, the socket will not be readable.
- T: One down/up pair on one focused synthetic window; same client connection performs `query_keymap()`, then a 50 ms socket select and bounded event collection. Preserve every event, including types without `detail`. Independent raw-only auditor checks queue count, socket readiness, exact target, keymap state, clock order, and Xvfb cleanup.
- D: PASS only if candidate exits 0, both edges have internal queue depth >=1 before select, socket is not readable at that point, both exact target events are recovered, keymap is true then false, clocks are ordered, and Xvfb exits 0. Otherwise STOP/FAIL; no rerun.
- C: The event may arrive only after the query reply, focus may be wrong, or server scheduling may make the socket readable; the synthetic fixture may not reproduce A03's event mix. A04 does not establish A03's precise cause.
- U: Synthetic Xvfb/Python-Xlib only; no real game, model, V39 task, useful-effect receipt, latency claim, or MAP01 outcome.
