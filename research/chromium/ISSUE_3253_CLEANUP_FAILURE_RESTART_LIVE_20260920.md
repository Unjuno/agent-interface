# Issue #3253 — live cleanup-failure control across restart (2026-09-20)

Additive control evidence for #3253. The original timeout/cancel restart result and all earlier artifacts remain unchanged.

## H/T/D/C/U

- **H:** If terminal receipt cleanup/release fails before orchestrator restart, the persisted terminal receipt must remain fail-closed; a fresh valid receipt must remain independently admissible.
- **T:** Three Docker `--network none` A→restart→B allocations using the pinned Chromium image, Xvfb, real Chromium, read-only CDP DOM oracle, and the pinned Xlib dependency. Container A wrote a journal with a timeout receipt whose release receipt was absent (`release_failed`), then exited. Container B loaded the journal and tested terminal replay plus a fresh-valid control.
- **D:** `PASS_CLEANUP_FAILURE_RESTART_AUDIT allocations=3 errors=0`. Journal/cleanup verification `3/3`; cleanup-failed terminal replay rejected with dispatch `0` and effect `false` `3/3`; fresh-valid DOM effect `3/3` (`saved:fresh-cleanup`). Raw SHA-256: `1218566e42b2f65cd34e5ca518eb39e862065718c619b2096688962474166acf`.
- **C:** `PASS_CHROMIUM_CLEANUP_FAILURE_RESTART_FAIL_CLOSED_SCOPED`. Missing cleanup/release evidence does not reopen terminal receipt authority after restart in this fixture.
- **U:** This is a bounded cleanup-failure control, not proof of every crash/journal durability mode or external orchestrator implementation. Broader generalization remains open.

The additive runner, raw trace, and independent auditor are under `research/chromium/timeout_cancel_restart_20260920/cleanup_failure_control/`.
