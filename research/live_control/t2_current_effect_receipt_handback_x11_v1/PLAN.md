# T2 live X11 current-effect receipt handback

Issue: #1492
Task: `T2-LIVE-X11-CURRENT-EFFECT-RECEIPT-HANDBACK-20260918-003`
Base: `7137efdf52093eedb792ad61d88d18930ea0ea06`

One factor after #1472: handback completion after the actuation receipt.

- `ACTUATION_RECEIPT_DRAIN`: complete at actuation-receipt receive.
- `CURRENT_EFFECT_RECEIPT_DRAIN`: wait for one independent typed `CURRENT_EFFECT` observation receipt for the same fresh session/request.

Both arms run the same independent X11 pixel observer. Effect receipts bind session/request/observer sequence/observation interval and carry `input_authority=false`, `semantic_authority=false`.

Positive formal corpus preserves #1472: +40 ms frontier return; offsets 34/36/38/39 ms; F8 hold 8 ms; app delays 0/3 ms; two reps/cell; 16 matched pairs /32 cases. Four immutable 8-case batches. A fifth immutable batch contains four NO_EFFECT candidate controls. Effect-receipt timeout is 8 ms after actuation-receipt receive. PASS speed gate: p95 <6 ms and max <8 ms. Reruns/replacements/tuning 0.

Construction is excluded: two positive matched pairs plus one NO_EFFECT control produced PASS-shaped mechanics; construction audit PASS.
