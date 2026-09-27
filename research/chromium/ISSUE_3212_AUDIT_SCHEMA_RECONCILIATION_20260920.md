# Issue #3212 audit schema reconciliation — 2026-09-20

Additive correction record. The original raw JSONL and prior reports remain unchanged.

## H/T/D/C/U

- H: The current main-branch independent audit must reject incomplete identity evidence and accept the same live result only when each X11 window row carries its display identity.
- T: Retrieved the original raw JSONL and current `audit.py` from main, ran the audit in `mixed-formal-2992-debian:20260920`, then added only the missing observed `display` field to each X11 window row in a separate corrected successor JSONL and reran the same Docker audit.
- D: Original raw: `HOLD_AUDIT rows=3 controls=3 errors=2`, both errors were positive-p2 identity correlation failures. Corrected raw SHA-256 `f9d4417ba9f281f0981cbb4a8ab5e0cfaa581353b299aad995d464bb12acb779`; current audit output: `PASS_AUDIT rows=3 controls=3 errors=0`.
- C: `HOLD_ORIGINAL_RAW_SCHEMA_INCOMPLETE`; `PASS_CORRECTED_LIVE_DISPLAY_AUDIT_SCOPED`. The original evidence is not silently rewritten; the corrected successor makes the observed display correlation explicit.
- U: Make the live runner emit the corrected schema directly, including `display` on every X11 window record, then repeat the allocation with a generated manifest rather than hand-derived JSONL.

## Raw audit results

```text
original:  HOLD_AUDIT rows=3 controls=3 errors=2
corrected: PASS_AUDIT rows=3 controls=3 errors=0
```
