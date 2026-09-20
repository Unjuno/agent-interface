# Run log — Issue #3772

## Formal-01 — STOP; direct xkbcomp returned 0 without active map change

- Allocation `issue3733-german-xkb-xkbcomp-apply-formal-01`.
- Fresh Xvfb :191 exposed XKEYBOARD/XTEST, baseline US. `setxkbmap -display :191 -print -layout de` generated a retained German map. `xkbcomp -w 0 - :191` consumed that exact stdout and returned 0 with empty stderr.
- Immediate query remained US; server dump and fresh Xlib map were unchanged from baseline. Runner stopped before US control; no candidate or XTEST input ran.
- Raw SHA-256: `e49dccfa63504c7bff35705495895fe2f0a240f099f6238f3b9c4062c8e8fe54`.
- Independent audit: `STOP_DIAGNOSTIC`, 0 integrity errors, 9 artifact files checked; finding `German_not_active`.
- This does not explain why both layout-application tools return success without a visible state transition, nor reconcile prior run-to-run discrepancy. No retry. A future diagnostic needs to establish server capabilities/extension behavior or use a different, directly observable application path before any candidate test.
