# Issue #4265 — live deterministic recovery guard after partial multi-key admission

## H
A typed recovery guard using admission state, independent application effect, and verified release can avoid harmful blind retry after partial/unknown/interrupted multi-key admission while preserving successful recovery when the state is sufficiently known.

## T
Linux x86_64 execution container; CPython 3.13.5; Tk 8.6; Python-Xlib 0.15; private per-case Xvfb with TCP disabled and XTEST input. No model/provider, user desktop/data, package install, shared runtime mutation, or experiment network.

Live app semantics are exact and frozen:
- first A press increments partial_side_effect;
- B press while A held increments intended_effect and removes one partial_side_effect;
- C press removes one known partial_side_effect and increments compensations.
A correct A+B ends intended=1, partial=0. A-only leaves partial=1.

Scenarios: NO_ADMISSION, PARTIAL_ADMISSION, FULL_ADMISSION, INTERRUPTED_AFTER_KEYS_HELD, UNKNOWN_OR_UNVERIFIED_RELEASE.
Policies: BLIND_RELEASE_AND_RETRY and EVIDENCE_GUARD.
Three repetitions, 5x2 cells = 30 fresh Tk/Xvfb sessions, three immutable 10-case batches. Each batch invoked once. Construction is excluded. No row retry/replacement/pooling/post-result tuning.

Candidate policy:
- NO_ADMISSION + verified release + zero effect -> release_all then A+B retry;
- PARTIAL_ADMISSION + verified release + exactly partial=1/intended=0 -> release_all, C compensation, verify partial=0/intended=0, then A+B retry;
- FULL_ADMISSION / INTERRUPTED_AFTER_KEYS_HELD + verified release + intended=1/partial=0 -> CONTINUE, no task retry;
- UNKNOWN_OR_UNVERIFIED_RELEASE -> safety release_all only, ABORT, zero postdecision A/B keypress.

Blind comparator retries every non-FULL state after safety release.

## D
PASS_PARTIAL_MULTIKEY_RECOVERY_GUARD_SCOPED only if:
- all 30 scheduled rows complete with app exit0, owned Xvfb terminal receipt, source bindings, and final A/B/C logical key neutrality;
- independent raw-only audit reconstructs app state from primitive key event history and typed predecision state;
- candidate unsafe/collateral recovery outcomes=0;
- candidate completes NO/PARTIAL/FULL/INTERRUPTED exactly in 12/12 candidate rows;
- candidate UNKNOWN cases are ABORT, intended=0, preserve existing partial=1 as unresolved, and emit zero postdecision task A/B KeyPress, 3/3;
- candidate PARTIAL cases compensate to partial0 before retry and end intended1/partial0, 3/3;
- candidate INTERRUPTED cases do not duplicate intended effect, 3/3;
- blind comparator unsafe/collateral outcomes exactly9: residual partial in 3 PARTIAL + duplicate intended effect in 3 INTERRUPTED + residual partial in 3 UNKNOWN;
- final neutral state 30/30;
- at least10 coherent copied-evidence mutations reject.
Any candidate duplicate intended effect, residual partial after claimed completed task, task retry under UNKNOWN release, final non-neutral key state, or raw/source/process contradiction is FAIL. Missing/timeout/setup evidence is STOP/HOLD.

## C
Cooperative Tk fixture with deliberately non-atomic semantics and one known compensation. The comparator is intentionally incomplete. X-server logical state is not physical HID telemetry. An ABORT can preserve a pre-existing unresolved partial application effect without being counted as a newly caused recovery collateral effect; this is explicit unfinished state, not success.

## U
No model decision quality, natural failure rate, arbitrary compensation safety, MAP01 benefit, token/latency advantage, cross-app/platform transfer, crash recovery or runtime promotion. #2129 remains open after any scoped result.
