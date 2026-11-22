# A02 execution deviation

`PREREGISTRATION.md` was drafted before implementation. During construction
tests, the oracle representation for F5/F6 was corrected: `expected_channels`
now records observed detections (empty for censored/missing cases), while
`latent_fault_channels` records the authored latent mechanism. The initial tests
had exposed that the earlier representation could conflate “expected detection”
with “observed detection.” The candidate function was exercised during those
development tests, and its outputs were not frozen then. Therefore A02 is
classified as an **exploratory development run**, not a preregistered formal
candidate/auditor allocation. The final CLI outputs and final-input hashes are
retained without implying preregistration.

The preregistered H/T/D scope was not broadened. This correction makes the
missing/censored truth representation explicit and preserves the initial test
failures in `DEVELOPMENT_HISTORY.md`; it does not rewrite their outcome.
