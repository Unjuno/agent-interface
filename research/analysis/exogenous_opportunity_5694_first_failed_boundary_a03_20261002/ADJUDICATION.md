# Post-run protocol adjudication — A03

The frozen candidate exited 0, the independent raw-only auditor exited 0, and its retained receipt is `PASS_METHOD_SCOPED` for exact replay of the nine authored ledger rows and rejection of all five frozen corruptions. Raw and audit bytes remain unchanged.

Before interpreting the result as support for H, I compared the phase controls against the frozen H. H requires cue phase to change while the capture schedule is held constant. That condition was not met: `phase_hit` has a single capture at 10 ms and horizon 50 ms; `phase_miss` has captures at 10 and 50 ms and horizon 60 ms. Therefore the observed `eligible_effect` versus `not_acquired` difference is only a descriptive classification of two authored traces; it does not isolate cue phase under a common capture schedule.

Final scientific disposition: **`HOLD_PHASE_CONTRAST_NOT_MATCHED`**. The raw-ledger replay/mutation gate passed, but H is not established and the phase-contrast component is not interpretable as preregistered. No source, fixture, raw output, auditor output, seed, or disposition was repaired or rerun. A future test would need a separately frozen successor with the exact same capture timestamps and observation horizon in both phase arms; this note does not authorize it.
