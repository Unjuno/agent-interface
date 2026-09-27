# #1459 T2 A9d in-flight receipt drain formal

Decision: **PASS_INFLIGHT_RECEIPT_DRAIN_SCOPED**

Formal discipline: 20 immutable batches x15 paired cycles = 300 pairs / 600 arm rows. Each batch invoked exactly once; reruns/replacements/tuning0. Exact global pair indices0..299 are retained once each.

## Result

- IMMEDIATE_TRANSFER post-transfer local completions: **61 / 300**
- IMMEDIATE_TRANSFER post-transfer effects: 61
- RECEIPT_DRAIN_TRANSFER post-transfer local completions: **0 / 300**
- candidate post-transfer effects: 0
- post-return admissions: 0
- subprocess nonzero exits: 0
- candidate drain p95: **2.420469 ms** (<4 ms gate)
- candidate drain max: **5.182661 ms** (<6 ms gate)
- independent audit errors: []
- corruption controls: 4/4 rejected

## Interpretation

In this same-host subprocess actuator model, closing new local admission at the +40ms frontier-return event is insufficient if frontier authority is considered transferred immediately: 61 pre-return admissions completed after that transfer point. Keeping the frontier return timestamp fixed while withholding authority-transfer completion until the matching local completion receipt eliminated all measured overlap.

This is a handback-contract measurement only. It does not establish XTEST cancellation, live GUI semantics, real frontier/model T2 usefulness, production latency, or cross-host clock behavior. The next smallest live question is transfer of the same receipt-drain rule to a fresh private-X11/XTEST allocation under #60; do not combine that transfer with a real model call.
