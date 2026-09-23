# Chromium reusable receipt successor audit

Issue: #3174.

## H/T/D/C/U

- H: retained guarded macro evidence can be reused safely only if a live session/resource receipt and fresh final gate are measured.
- T: fetch the current-main frozen Chromium procedure source, run formal_runner.py once in a network-disabled Python 3.12 container, then run audit.py independently over the retained 12 rows.
- D: formal invocation 1, 12 rows, audit errors empty, formal rows SHA-256 69d54d36fba48c984d667b34fbc6ad2af83ddf4c88c282ece59b4d0694387e62. Source hashes are in RESULT.json.
- C: HOLD_REUSE_BENEFIT_UNMEASURED. The Docker run reproduces the guarded-macro retained replay, but it does not launch Chromium or measure reusable receipts, session restart, transplant, model-wait invalidation, fresh final gate, or live application effect.
- U: do not promote PASS_CHROMIUM_GUARDED_MACRO_COMPILATION_SCOPED to #3174. A future run needs an executable Chromium fixture and live receipt/effect trace.

No new model or network calls were made. The retained macro audit result is preserved as a separate scoped result.
