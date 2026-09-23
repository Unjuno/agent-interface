# Issue #3253 — live timeout/cancel receipt replay across orchestrator restart (2026-09-20)

Additive successor evidence for #3212. Earlier timeout/cancel, STOP, and HOLD records remain unchanged.

## H/T/D/C/U

- **H:** A persisted timeout/cancel terminal receipt must fail closed after orchestrator restart, while a fresh valid receipt remains independently admissible and produces the live effect.
- **T:** Three A→restart→B Docker allocations using `mixed-formal-2992-debian:20260920` (`sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`) with `--network none`, Xvfb, real Chromium, read-only CDP DOM oracle, and pinned `python-xlib==0.33` mounted read-only for XTEST support. Container A wrote a receipt journal containing timeout, cancel, and fresh-pending entries, then exited. Container B loaded the journal after restart and evaluated all replays.
- **D:** `PASS_TIMEOUT_CANCEL_RESTART_AUDIT allocations=3 terminal_replays=6 errors=0`. Journal load `3/3`; timeout/cancel replay rejection `6/6` with admission `0`, XTEST dispatch `0`, and DOM effect `false`; fresh-valid admission/effect `3/3`; Xlib dependency loaded `3/3`. Raw SHA-256: `58489f28041677a73cd9cf723772aa42e7798e7e13d8a95070ecf92221c2c778`.
- **C:** `PASS_CHROMIUM_TIMEOUT_CANCEL_RESTART_FAIL_CLOSED_SCOPED`. Terminal receipt state remains fail-closed across this orchestrator restart fixture, while fresh-valid remains live.
- **U:** This does not prove arbitrary crash consistency, cleanup-failure semantics, or cancellation propagation in every external orchestrator. The journal and fixture are intentionally bounded; broader production generalization remains open.

The additive runner, fixture, raw journal result, and independent auditor are under `research/chromium/timeout_cancel_restart_20260920/`.
