# T2 live X11 A2 — receipt drain vs effect tail

Issue: #1472
Task: `T2-LIVE-X11-RECEIPT-DRAIN-EFFECT-TAIL-A2-20260918-002`
Base: `c2826ec7cfb2aceaf55c9ef0e6fe1e9ed301692c`

This additive private-X11 experiment preserves #1468's two handback arms and changes only the primary held-input occupancy evidence to #981 dual-edge XSync intervals.

- DOWN interval: `[down_call_ns, down_return_ns]`
- UP interval: `[up_call_ns, up_return_ns]`
- guaranteed physical occupancy: `[down_return_ns, up_call_ns)`
- possible physical occupancy: `[down_call_ns, up_return_ns)`

The independently sampled X keymap remains secondary evidence. The independent pixel observer determines the first visible RIGHT-state effect.

Formal corpus: frontier return +40 ms; admission offsets 34/36/38/39 ms; 8 ms F8 hold; app processing delay 0/3 ms; two reps/cell; 16 matched pairs / 32 cases, counterbalanced. Four immutable 4-pair batches; no reruns/replacements/tuning.

Decision labels are exactly those in Issue #1472. Construction produced `HOLD_EFFECT_TAIL_AFTER_ACTUATION_DRAIN` with mechanics audit PASS and is excluded from the formal denominator.
