# Post-formal audit correction

The frozen runner and `audit.py` each emitted a readiness PASS. A separate
post-formal adversarial check compared every visible-window owner PID in the
raw identity records against the launched/reaped process ledger. It verified
the raw SHA-256, found that Inkscape PID 11 and Chromium PID 118 were tracked,
but Calc's visible main window owner PID 95 did not match the tracked
LibreOffice launcher PID 66 (exit 255). No lifecycle receipt for PID 95 is
present. The X server socket is absent, but that does not prove the Calc
window-owner process was reaped by the experiment runner.

Correct final classification: `HOLD_PROCESS_LIFECYCLE_UNVERIFIED`. This is an
evidence-completeness HOLD, not a claim that the visible identity was wrong or
that the readiness hypothesis failed. The initial pass outputs remain
immutable and retained; `audit_lifecycle.json` records the correction.

One documentation limitation is also disclosed: the construction-only
preflight stdout was summarized in `PREREGISTRATION.md`/`PRECHECKS.md`, not
saved as a byte-for-byte raw artifact. The formal run has its own complete raw
window snapshots and is unaffected by this construction-data limitation.

No formal allocation was rerun, no source/threshold was tuned after the run,
and no cleanup is being inferred from Docker container deletion beyond the
verified X socket disappearance.
