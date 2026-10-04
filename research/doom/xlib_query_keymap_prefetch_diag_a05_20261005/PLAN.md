# A05 predeclared protocol

- H: In an isolated Ubuntu arm64 Xvfb fixture, synchronous `query_keymap()` after each injected edge returns with the exact corresponding client event already in Python-Xlib's internal queue, while the X socket is not readable.
- T: One down/up pair on a focused synthetic window. Serialize all queue entries before select; preserve arbitrary types and optional fields. Then collect the exact expected event with a one-second bound. Raw-only auditor validates that the exact target was in the pre-select snapshot, keymap sequence, socket readiness, clock order, and clean Xvfb exit.
- D: PASS only if candidate exits 0, both pre-select snapshots contain the exact corresponding event, queue depths are positive, socket is unreadable, state is true then false, clocks are ordered, and Xvfb exits 0. Otherwise STOP/FAIL; no retry.
- C: Scheduling, focus, and event queue contents may differ; another event may be prefetched while target is not. A05 cannot prove A03's cause if that event mix is not recreated.
- U: Synthetic Xvfb/Python-Xlib only; no game, model, V39 task, useful-effect receipt, latency claim, or MAP01 outcome.
