# Issue #5970 T8 — Tk ancestor observer

## Disposition

`STOP_OBSERVER_READY_TIMEOUT` before any synthetic input. The exact-source-derived Tk app reached its focused ready state, but the ancestor-enumerating observer did not produce its readiness line within the bounded five-second wait. No keycode was resolved, no X RECORD context or XTest event was started, and no release was needed. The runner preserved the pre-input STOP and empty record stream.

The one auditor invocation also STOPped because it assumed a non-null observer-ready object and raised `AttributeError` on this candidate STOP. This auditor construction failure is retained in the execution transcript; no corrected/repeated candidate or auditor was run. T8 has no inferential result. T9 is a separately frozen immediate-parent successor; it does not overwrite this STOP.

Possible causes (recursive query cost, event-mask sync/error behavior, or observer process failure) remain unresolved. No production, physical-input, recovery, or task-benefit claim.
