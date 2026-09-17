# Typed readiness-state contract — first outcome

Task `READINESS-TYPED-STATE-CONTRACT-20260918-001`, Issue #1197, parent #48.

## Decision

**`PASS_TYPED_READINESS_STATE_SCOPED`**

One source-first deterministic formal invocation, reruns0. No model/provider/network/GUI/X11/task-input/shared-runtime action occurred.

## Frozen factor

The same underlying readiness evidence is exposed in two representations:

- `READY_BOOL`: only READY_FOR_ACTION is true; every other condition becomes false.
- `TYPED_READINESS`: READY_FOR_ACTION, READY_FOR_OBSERVE, LOADING, BLOCKED_MODAL, TARGET_UNAVAILABLE, STARTUP_FAILED, RESET_REQUIRED, UNKNOWN.

Readiness is evidence only. It never grants input authority. Pixel class is a non-authoritative HINT and cannot by itself establish READY_FOR_ACTION.

Frozen bounded recovery mapping:
- READY_FOR_ACTION -> PROCEED_TO_ORDINARY_ADMISSION
- READY_FOR_OBSERVE -> OBSERVE
- LOADING -> WAIT_BOUNDED
- BLOCKED_MODAL -> HANDLE_OR_ESCALATE_MODAL
- TARGET_UNAVAILABLE -> REACQUIRE_TARGET
- STARTUP_FAILED -> RESTART_OR_FAIL_SETUP
- RESET_REQUIRED -> RESET_ENVIRONMENT
- UNKNOWN -> OBSERVE_OR_YIELD

## Formal first outcome

300,000 rows = 25,000 ×12 frozen strata.

- candidate/oracle mismatch: 0
- authority promotions: 0
- pixel-only READY promotions: 0
- stale-evidence READY promotions: 0
- typed recovery mismatch: 0
- malformed rows retained: 25,000
- READY_BOOL false aliases: 7 distinct recovery classes
- best deterministic single `false -> one action` error: **150,000 rows**

The boolean error is a representation-collision result, not a claim that every binary-ready system would choose one fixed recovery action. It establishes that the single false bit alone does not carry enough information to select the frozen bounded recovery class.

State counts:
- READY_FOR_ACTION 50,000
- READY_FOR_OBSERVE 25,000
- LOADING 25,000
- BLOCKED_MODAL 25,000
- TARGET_UNAVAILABLE 25,000
- STARTUP_FAILED 25,000
- RESET_REQUIRED 25,000
- UNKNOWN 100,000

## Integrity

- RESULT SHA-256 `345bb26cb720c1322da7d4176a7feb35a3b70ccb9b90ed4cae8b7ec615f44453`
- AUDIT SHA-256 `20fef1d34892ee4694acea82688d0a6661cf0f311af64fc6ab8f645689a87c81`
- CORRUPTION SHA-256 `89534230fe856cab199914c77ade102220705f8d4f7f7a2c8010adbbbffbd811`
- SOURCE_REHASH SHA-256 `b5dab49ebbb4da32689c1303b63edc450ba0a3e2ce6304e54ab082f67701ffff`
- audit PASS/errors[]
- copied-result corruptions7/7 reject
- frozen source rehash7/7 exact

## Boundary

This validates typed readiness/recovery representation mechanics only. It does not prove the upstream evidence detector can correctly classify a real loading screen, modal, startup failure or target absence.

The next #48 rung should transfer this fixed vocabulary to controlled delayed-paint/loading/startup-failure fixtures while keeping authority and recovery semantics unchanged. Do not add a model or planner-policy change in the same allocation.
