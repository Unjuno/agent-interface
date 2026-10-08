# Recovery status for #2858 Rung0

This additive record preserves the abandoned frozen mechanism-screen source. It
does not close #2858 and does not claim an experiment result.

- The owner recorded the frozen formal allocation at **0/24**; no formal row
  had run. The exact one-shot command remains in the Issue history. This
recovery did not start it or consume the allocation.
- The frozen environment requires CPython 3.13.5 and Chromium 144.0.7559.96 on
  the recorded Linux image. The locally available browser/Xvfb/Openbox image we
  checked has Python 3.12.14 and Chromium 154; it is not an equivalent
  environment, so no substitute formal run was attempted.
- This Rung0 plan is explicitly only an internal-page mechanism screen. It does
  not meet #2858's required second desktop-like held-out surface or reproduce
  #2416's original six-task fixture and cannot establish the Issue acceptance
  boundary by itself.
- The original seven frozen files and their historical hashes are preserved
  unchanged. No formal evidence or first outcome is available in this recovery.

Disposition: `HOLD_NOT_RUN_ENVIRONMENT_MISMATCH`. A fresh, correctly frozen
successor with the required environment and full #2858 acceptance coverage is
needed before reporting an experiment result. Do not interpret this HOLD as a
scientific failure or as completion of #2858.
