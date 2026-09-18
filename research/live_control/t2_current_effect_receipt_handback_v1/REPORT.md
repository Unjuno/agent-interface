# T2 live X11 current-effect receipt handback — duplicate allocation record

Issue #1494. This branch preserves a completed duplicate allocation caused by a coordination race with earlier owner #1492.

## Overall disposition

`STOP_DUPLICATE_FORMAL_ALLOCATION` — **not promotion-eligible and must not be pooled with, replace, or overturn #1492**.

#1492 was created and claimed first under the same task ID `T2-LIVE-X11-CURRENT-EFFECT-RECEIPT-HANDBACK-20260918-003`. Immediately before this branch launched formal, its ownership reread had not yet returned the newly-posted collision note; the four immutable batches were then consumed once. The raw first outcome is retained here rather than erased. The scientific sub-audit below is descriptive only because the allocation duplicated an already-owned task.

## Descriptive sub-audit

Under #1494's separately frozen gates, the one consumed allocation produced `PASS_CURRENT_EFFECT_RECEIPT_HANDBACK_SCOPED`; formal invocation 1; reruns/replacements/tuning 0; 16 matched pairs /32 cases.

- ACTUATION_RECEIPT_DRAIN: effect after handback 16/16; local completion after handback0/16; possible/guaranteed physical occupancy after handback0/16; correct/released16/16.
- CURRENT_EFFECT_RECEIPT_DRAIN: effect after handback0/16; local completion after handback0/16; possible/guaranteed physical occupancy after handback0/16; typed receipt valid16/16; correct/released16/16.
- Candidate added wait after actuation receipt: p50 2.055852 ms; max 3.751476 ms.
- app-delay0 added wait: p50 0.576607 ms; max 0.774305 ms.
- app-delay3 added wait: p50 3.516424 ms; max 3.751476 ms.
- Independent scientific audit: PASS/errors[].

These numbers **cannot** be used as a rerun of #1492. #1492's legitimate first formal outcome is `HOLD_EFFECT_RECEIPT_TOO_SLOW`, including a scheduler-delayed 20.341329 ms receipt wake and four NO_EFFECT controls. The differing outcomes reinforce why duplicate allocations must not be selected between.

## Integrity

FORMAL_RESULT SHA-256 `f18bb2840943daa83fc7ffcbca8588c4533f14b405f87bb8df1df01e429135a5`.
Gzip SHA-256 `eafc024cb26fa0513210b553dce445dfc5ed24067f4e7daa9553b0c291f44a9e`.
AUDIT SHA-256 `0d0c671e2389bb34baa2482c291728e6fe04e2dd4d0dab6c2b9f1e83234a4a09`.
Full raw rows remain in `FORMAL_RESULT.json.gz.b64`.

A separate preformal publication-byte mismatch in `experiment.py` was detected and repaired before any formal batch; final source readback matched the construction bytes.

## Scope / successor

No main integration is requested for this duplicate branch. The valid scientific successor follows #1492's retained HOLD: preserve its 8 ms absolute timeout and change only deadline enforcement so a scheduler-delayed queue wake cannot accept a receipt after the absolute monotonic deadline.
