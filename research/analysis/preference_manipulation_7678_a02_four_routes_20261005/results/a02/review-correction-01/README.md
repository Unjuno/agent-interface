# Read-only audit correction 01

The frozen formal auditor invocation failed before reconstructing the matrix because its dynamic module loader did not set `__file__`. The original failure is retained unchanged in `../INITIAL_AUDIT_FAILURE.json`; the candidate output and frozen scripts were not edited, and neither the candidate nor formal auditor was rerun.

This version sets `__file__` for the frozen independent #6274 auditor and independently recomputes the retained 6,624-row candidate output. It is an additive, post-run audit of existing bytes, not a confirmatory allocation rerun. The formal A02 disposition remains `HOLD_AUDITOR_STARTUP_ERROR` regardless of this diagnostic result.
