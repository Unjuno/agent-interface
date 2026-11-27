# WSLc MAP01: gray-overlay threshold controls

Four preregistered independent episodes use a fixture fire action at (636,526) for 500 ms, with no model. In each episode an opaque RGB(128,128,128) 8x8 X overlay is mapped after the first held-key capture. Each of two seeds is tested at thresholds 32 and 150, ordered 32/150 then 150/32. Candidate and target are fixed, but episodes and timing are independent. The source snapshot is not asserted identical to main; the pre-dispatch guard stays at 32.

| Seed | Threshold | Gray patch mean difference | Outcome | Ammo |
|---|---:|---:|---|---|
| 991037 | 32 | 105.542 | cancellation requested | 50 to 49 |
| 991037 | 150 | 105.542 | completed; no cancellation | 50 to 48 |
| 991038 | 150 | 109.776 | completed; no cancellation | 50 to 48 |
| 991038 | 32 | 109.776 | cancellation requested | 50 to 49 |

Every run verified neutral input; cancelled actions have unknown partial effect. All four recorded one hit and 15 damage. The overlay's pixel values and mapped time are independently recorded and checked against the sampled frames. Thus, in these trials the raised threshold failed to react to a deliberate change detected at threshold 32. The overlay is synthetic and not labeled as a real hazard; these observations do not establish error rates, optimal threshold, semantic safety, model performance, or MAP01 completion. Combined with the previous natural-change results, they demonstrate the sensitivity/interruption trade-off and motivate event-aware controls rather than promoting a threshold to production.

`public.zip` retains conditions, frozen sources, fixture messages, images, raw observations and action/release receipts. SHA-256: `3c6edb3515d7b49eb006b888c3d19401a372966e18a20e5081bce563a17e6053`. Run `python audit.py` without `-O` (Pillow required) to recompute image differences and check overlay timing, guards, cancellation, releases and counters. All hosts and containers exited and WSLc listed no active allocations.
