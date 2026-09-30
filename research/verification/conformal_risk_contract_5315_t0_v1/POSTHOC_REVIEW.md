# Post-hoc review addendum — formal01

This addendum does not alter the frozen source commit, `RESULT.json`, or the
first audit STOP. It records a separate adversarial review performed after the
corrected raw-only audit passed.

## Newly found checker defect

The original H requires immutable calibration binding. `candidate.py` only
checks that `calibration_digest` is a non-empty string; it does not recompute
the digest or compare it with retained calibration content. A new, read-only
negative control changed the digest to `sha256:tampered-nonempty` while leaving
all other fields unchanged. The frozen checker returned
`ALLOW_MARGINAL_CLAIM_ONLY` (exit 0). This falsifies the frozen hypothesis and
fails the intended digest-binding gate. The result is preserved; there was no
formal rerun and no change to the candidate or formal raw.

## Disposition

- Scoped arithmetic boundary: reproduced; the given CRC finite-sample
  expression is 0.045 at alpha 0.05.
- Selective-risk boundary: reproduced in the fixed IID fixture; marginal loss
  is 0.04 while conditional risk among selected singleton claims is 1.0.
- Applicability rejection: all four declared shifted/adaptive rows are
  rejected, but the checker is not robust to calibration-digest tampering.
- Overall H/D: **FAIL / do not use as a certificate checker**. The original
  output is useful only as a counterexample and arithmetic record.
- First independent audit STOP and corrected audit are both retained. The
  corrected audit did not include digest-tamper coverage; the post-hoc review
  closes that gap without rewriting the audit history.

The next allocation, if pursued, must be a distinct additive successor with a
digest checked against retained calibration bytes, a mutation control for
those bytes, and an independent auditor that recomputes the binding. This
synthetic host-only T0 does not implement SCRC or validate any production
population.
