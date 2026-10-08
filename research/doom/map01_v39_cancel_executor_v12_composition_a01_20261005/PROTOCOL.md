# A01 protocol: V13 cancellation receipts through current ExecutorV12

## H / T / D / C / U

**H.** The PR #7805 V13 owner/bridge candidate can pass per-key cancellation-release receipts through the exact current-main `ExecutorV12` asynchronous release barrier without duplicate aggregate publication or a terminal-order violation.

**T.** Freeze current main `16c74566b64f32d7fe035c7724bcfe3865863a91`, candidate source PR #7805 head `9d14deb26587da662a085b9d139310a386e6cf5a`, and the SHA-256 values in `SOURCE_LOCK.json`. Run one fake-display cancellation composition: admit an F8 hold, cancel after the fake physical down is acknowledged, capture all owner and executor events, and audit the retained event stream. No real display, application, game, or OS input.

**D.** Scoped PASS requires exactly one confirmed per-key physical-up receipt bound to the admitted id/step/token and actuation id; exactly one verified empty aggregate `input_released`; both release records precede the single cancelled terminal; fake physical and backend-held key sets are empty; and no event grants input authority. Any missing, duplicate, unverified, or post-terminal receipt is FAIL. A harness/import/precondition failure before candidate execution is STOP. There is one candidate execution only.

**C.** Test-only fake Xlib modules and an in-process `ExecutorV12` with its actual lease/release barrier. The bridge superclass is stubbed only at the execute/release seam; its existing typed backend does not perform captures here. The owner candidate and the executor are loaded from frozen source.

**U.** Synthetic construction/integration evidence only. It does not show live X11 physical release, game/application consumption, independently useful feedback, recovery, threat response, latency, MAP01 progress, or safety. The container attempt stopped before startup because OrbStack could not read the cached image blob (`operation not supported`); native Python is explicitly a fallback, not container-equivalent evidence.

## Execution discipline

The image attempt is not retried. `run_candidate.py` is invoked once and refuses to overwrite its output. If it exits nonzero, retain that first outcome and do not rerun. The independent auditor consumes only the saved JSON and does not execute candidate code.

## Run 02 delta

Runs 01–03 stopped before candidate code was loaded due to runner setup defects (root path, helper lookup, then fixture class lookup). Every STOP is retained in its original output directory; no consumed path is reused. A later auditor path bug also left a duplicate audit JSON in formal_01; its hash is documented in that STOP record and formal_04/audit.json is canonical. After repeated harness-authoring errors, run 04 uses the fixture class returned by the existing fixture loader and a fresh identity/output path. It remains native-Python fallback evidence.
