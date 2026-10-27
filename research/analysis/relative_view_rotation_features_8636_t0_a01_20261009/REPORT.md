# T0 A01 result — Issue #8636

**Disposition: `HOLD_UNCERTAIN` (the independent audit did not complete).**

The candidate invocation completed with exit code 0 and emitted all 360 scheduled arm trials. The one independent auditor invocation exited 1 before writing `audit.json`. Its first reported mismatch is the raw-pixel arm on focal-shift seed 30011, observation 0: the controller returned `YIELD` with reason `feature shape changed`. This is an out-of-calibration stress observation. The preregistered auditor rejects any YIELD outside the feature-loss fault list, so it rejects a behavior the protocol permits the image correspondence gate to fail closed on during focal shift. The remaining recorded events have not been accepted as independently audited evidence.

Accordingly, `PASS_METHOD_SCOPED`, `H_SUPPORTED_SCOPED`, and `H_FAIL_SCOPED` were not established; no hypothesis comparison is reported. The raw first outcome is preserved without rerunning either program. The mismatch points to a preregistration/auditor contract defect, not a demonstrated controller failure or success. A corrected audit would need a new, explicitly versioned allocation and freeze.

The finding is confined to this synthetic CPU fixture. It says nothing about live computer input, GUI/game control, application acknowledgement, task effect, latency, safety, or product readiness.

See `FORMAL_RUN.md` for invocation receipts and artifact digests. The exact raw first outcome is `results/first-outcome.tar.gz`.
