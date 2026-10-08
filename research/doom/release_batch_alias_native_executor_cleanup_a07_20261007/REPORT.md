# A07 — native Xvfb executor cleanup after alias refusal

**Outcome: `STOP` (preserved; no retry).** The candidate ran once in the pinned private Xvfb image with network disabled, a read-only source mount, a separate writable results mount, and 2 CPU / 4 GiB limits. It failed during its `finally` block because it attempted to write `A07_RAW.json` under `/study/results`, which was mounted read-only, instead of `/out`. The exact container error and exit code are preserved in `results/A07_RAW.json` and `EXECUTION_RECEIPT.json`.

This run does **not** establish whether the action was admitted, whether the alias guard fired, whether V13 published a terminal, whether release was verified, or whether Xvfb/owner cleanup completed. Those values are unknown. The auditor reports `STOP`; it is not a cleanup pass. The one-shot policy prohibits rerunning the candidate, so the mount-path defect remains an unresolved harness issue.

The candidate was designed to exercise a candidate-only duplicate-keycode guard through the actual V4→V3→V12 owner and V13 executor on private Xvfb. Production source snapshots are hash-pinned to `origin/main` `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`; the only behavior change is in the candidate-only owner copy. The guard was not integrated into production.

No game, desktop session, model, physical keyboard, or shared live allocation was used. This STOP does not satisfy Issue #59's MAP01 live gate. It must remain separate from A06's fake-X PASS and A03's manual-close Xvfb PASS.

## Reproduction and retained evidence

`FREEZE.json` records the hypothesis, method, source hashes, image digest and one-shot rule. `EXECUTION_RECEIPT.json` records the exact container configuration and failure. `results/A07_RAW.json` preserves the container error; `results/A07_AUDIT.json` is a read-only audit of that STOP. No candidate rerun occurred.

## Append-only correction (2026-10-07)

Static execution-order review found that the candidate never reached `Executor.submit()`: `Backend.__init__` evaluated `Lease(window.id)`, but `window` is local to `main()` and unavailable in that method's module-global scope. The resulting `NameError` was caught, then masked when `finally` attempted the incorrect read-only `/study/results` write. Therefore no input action was submitted. The exact first exception was not retained in the container output; the `NameError` diagnosis is source-based. A07 remains STOP and was not rerun.
