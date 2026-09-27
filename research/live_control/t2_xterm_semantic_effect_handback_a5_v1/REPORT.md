# XTerm semantic-effect handback A5

Issue #1555. Fresh one-factor successor to #1553. Only pre-frontier scheduling changed to hybrid absolute wait; semantic contract, corpus, deadlines, batching and terminal QueryKeymap evidence were unchanged.

## Construction

`PASS_CONSTRUCTION_ELIGIBLE` on the tight offset39 boundary: actual press 39.305–39.641 ms, terminal x-UP4/4, exact PTY input/focus/exit0, positive receipts3/3, NO_EFFECT timeout.

## Formal first outcome

All five immutable batches completed once; reruns/replacements/tuning0.

- rows36; positive pairs16;
- baseline semantic effect after completed handback16/16;
- candidate valid semantic receipts16/16;
- candidate semantic effect after completed handback0/16;
- candidate positive timeouts0;
- candidate release timestamp before handback16/16;
- NO_EFFECT receipts0/4, completed handbacks0/4, timeouts4/4;
- exact PTY input, focus readback, helper/XTerm exit0, terminal QueryKeymap x-UP and press-before-frontier all36/36;
- actual press offsets34.255364–39.591349 ms;
- candidate drain p95 **6.110989 ms**; max **8.270676 ms**.

Frozen speed gates were p95<6 ms and max<8 ms. Both are missed.

Disposition: `FAIL_XTERM_SEMANTIC_EFFECT_HANDBACK_A5_SPEED_GATE`.

This is a scientific negative at the frozen same-host envelope, not a harness stop. The semantic-effect drain eliminated post-handback semantic tail and false-positive handback, but did not meet the fixed latency budget. Do not retune the consumed A5 allocation. A future successor must pose a genuinely new envelope/architecture question rather than relaxing thresholds post hoc.

## Scope

Private Xvfb/XTerm/raw-PTY/XTEST only. No model/provider/network/user desktop/MAP01/shared runtime; no general GUI or production claim.
