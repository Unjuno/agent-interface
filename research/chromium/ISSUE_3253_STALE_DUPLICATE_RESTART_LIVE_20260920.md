# Issue #3253 — live duplicate-terminal and stale-generation replay after restart (2026-09-20)

Additive completion evidence for the remaining replay cases. Earlier artifacts remain unchanged.

## H/T/D/C/U

- **H:** After orchestrator restart, a previously dispatched terminal receipt and a receipt from a stale source generation must both fail closed; a new generation receipt must remain admissible.
- **T:** Three Docker `--network none` A→restart→B allocations with Xvfb, real Chromium, pinned Xlib/XTEST dependency, persisted journal, and independent CDP DOM oracle. A wrote duplicate-terminal, stale-source-generation, and fresh-after-restart entries; B loaded and replayed them.
- **D:** `PASS_STALE_DUPLICATE_RESTART_AUDIT allocations=3 errors=0`. Journal load `3/3`; duplicate-terminal replay rejection `3/3`; stale-source replay rejection `3/3`; both classes had dispatch `0` and effect `false`; fresh-after-restart DOM effect `3/3` (`saved:fresh-after-restart`). Raw SHA-256: `f2444119917d201568475a82ce4bed3f0b3bb1371214f4965faedbd86f46c28`.
- **C:** `PASS_CHROMIUM_STALE_DUPLICATE_RESTART_FAIL_CLOSED_SCOPED`. The remaining replay classes fail closed across the restart fixture while a new receipt remains live.
- **U:** This is bounded journal/restart evidence, not universal crash consistency or production orchestrator proof. Broader generalization remains open.

Runner, fixture, raw trace, and independent auditor are under `research/chromium/timeout_cancel_restart_20260920/stale_duplicate_control/`.
