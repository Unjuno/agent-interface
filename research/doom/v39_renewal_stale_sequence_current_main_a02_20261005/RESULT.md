# Result — frozen-source stale-renewal rejection A02

**Disposition: `FROZEN_SOURCE_STALE_RENEWAL_REJECTION_REPRODUCED`.** The exact V39 controller snapshot captured from main at `b6907899f11b036f2af572e8d4794ebb4b7e5c83` reproduces A01's stale sequence boundary in both normal Python 3.12 and optimized `python -O`. This is evidence for that frozen source only; it does not establish behavior on today's main or how often the race occurs.

## H/T/D/C/U

- **H:** If an observation with sequence 8 arrives while the V39 controller is waiting for renewal acknowledgement submitted against sequence 7, the stale-sequence rejection is raised as `RuntimeError` rather than retained as a typed renewal disposition.
- **T:** Reused the unchanged A01 AST-extracted `wait`, `submit_cover`, and planner renewal block against the exact frozen controller snapshot snapshot, together with the exact frozen `ControllerFailureCleanup` helper. Injected prior cover `cover-0` expired with a verified empty release, then observation sequence 8, then rejection of `cover-0-renew-1` because latest sequence is required. Ran normal and `-O` modes with zero retries; no game, model, GUI, X server, native input, container, or allocation.
- **D:** Reproduction required the exact rejection/exception, no renewal admission and no planner interrupt before cleanup; prior cover release reconciled verified-empty; failure cleanup closes the planner only after its await returns and remains incomplete because scorer terminal, score file, and owner-close evidence are absent. **All 21 independent audit checks passed** over both retained outcomes and the two frozen source blobs.
- **C:** This is a constructed FIFO boundary, not a probability estimate. In a natural run, the executor can reject stale input safely; the unresolved behavior is controller recovery/liveness and complete terminal accounting, not unsafe new input admission.
- **U:** It proves only the current-main source path under this synthetic event schedule. It does not prove a live game event, pending/rejected renewal physical release, scored result, event frequency, useful feedback, recovery benefit, task effect, MAP01 progress, or a repair.

## Observed sequence

For both interpreter modes, the retained event order is: planner await started → prior cover terminal consumed → sequence 8 observation consumed → stale renewal rejection consumed → planner await returned → failure cleanup closed planner. The controller raised `RuntimeError` with reason `latest observation sequence required before input`, recorded zero planner interrupts, and admitted no renewed cover. The prior accepted cover's terminal says release verified empty. Cleanup marks input terminals complete and verified-empty history, but `cleanup_complete=false` because scorer terminal, score file, and owner event closure are absent.

This is a bounded failure/recovery-accounting gap worth carrying into the candidate-controller review. It does not, by itself, prescribe reusing the old policy: any continuation must either receive a fresh model-authored policy or explicitly yield/stop with complete cleanup evidence.

## Reproduction and evidence

- Freeze: `FREEZE.json` (controller blob `e9b437979e87347f6aa4dbefffcc84e9a2d01752`, cleanup blob `d04e167ed182d5faf935e6c23132b164fe9a16ac`).
- Command: `python run_checks.py`.
- Raw: `PROCESS_RESULTS.json`, `test_normal.*`, `test_optimized.*`, `observed_normal.json`, `observed_optimized.json`, and `py_compile.*`.
- Independent audit: `audit_currentmain_a02.py`, `AUDIT.json` (21/21), `SHA256SUMS.txt`.
- `AUDIT_REPAIR_NOTE.md` preserves the first audit harness path-mapping error. It stopped before reading candidate output; no candidate test was rerun for that audit correction.

No production source was changed; there is no PR or main update from this construction. The previous A01 result remains unchanged.
# Addendum — current-main applicability check

A02's normal and optimized runs remain reproducible evidence for the frozen source at `b6907899f11b036f2af572e8d4794ebb4b7e5c83`. A later repository state was checked on 2026-10-05: `origin/main` is `5339abda428b426a7e646dbd3f17f3a62c960584`, and the A02 controller and cleanup blobs do not match the corresponding current-main source snapshots. Therefore A02 is **not** evidence that current main still has the reproduced behavior. A subsequent fix commit `fc14994f53655da57b9b6573d028ddde1a11b858` exists in the local fetched history but is not an ancestor of `origin/main`; validate that candidate independently before adoption. No A02 tests were rerun for this identity check.

