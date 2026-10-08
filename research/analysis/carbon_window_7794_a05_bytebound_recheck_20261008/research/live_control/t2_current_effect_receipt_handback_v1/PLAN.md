# T2 live X11 successor — current effect receipt before handback

Issue: #1494
Task: `T2-LIVE-X11-CURRENT-EFFECT-RECEIPT-HANDBACK-20260918-003`
Base: `7137efdf52093eedb792ad61d88d18930ea0ea06`
Parent: #1472 `HOLD_EFFECT_TAIL_AFTER_ACTUATION_DRAIN`.

One factor only: replace actuation-receipt handback completion with a handback that also waits for an independently produced, case-local typed current-effect receipt from the existing pixel observer. Parent fixture, F8 action, +40 ms frontier return, offsets 34/36/38/39 ms, 8 ms hold, app delays 0/3 ms, XSync dual-edge occupancy semantics, and final scorer are unchanged.

Formal corpus: 16 matched pairs / 32 fresh cases, counterbalanced, four immutable 4-pair batches. One logical formal allocation; reruns/replacements/tuning0.
