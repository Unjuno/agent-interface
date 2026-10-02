# Freeze-only archival qualification — Issue #4064

Exact `FREEZE.json` from `research/referenced-image-retention-budget-20260922` at `90f2c574831fab0e4f503fede81f8785c4845f8c`; source Git blob `37c72b44f59c1c51013d1ac76fd270dd32418268` is preserved unchanged.

- **H:** retain the 36-case allocation identity/source hashes and prevent accidental duplicate execution.
- **T:** the remote branch contained only this freeze. Issue #4064 reports a scoped 36-case PASS, but the frozen code, two raw batches and audit package are unavailable; the two identified Actions runs have no artifacts. No formal rerun was performed.
- **D:** `HOLD_SOURCE_AND_RAW_UNAVAILABLE`; metadata preservation only, not independent reproduction or result promotion.
- **C:** the report and freeze can guide recovery but cannot substitute for missing observations and executable sources.
- **U:** repository-restorable formal bytes and independent audit remain absent. Issue #4064 remains open.

Original branch history is archived at `archive/recovered/referenced-image-retention-budget-4064-20260922`.
