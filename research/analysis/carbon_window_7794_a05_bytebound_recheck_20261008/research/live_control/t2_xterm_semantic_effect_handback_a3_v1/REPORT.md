# XTerm semantic-effect handback A3

Issue #1548. Fresh successor to #1541; A2 partial sessions pooled0. Only outer packaging changed to four immutable positive batches plus one NO_EFFECT batch.

## Execution

All five batches executed exactly once and serialized before aggregation. No batch reruns/replacements/tuning.

Observed aggregate:
- positive pairs16 / positive cases32;
- baseline semantic effect after completed handback16/16;
- candidate valid semantic receipts16/16;
- candidate semantic effect after completed handback0/16;
- candidate positive timeouts0;
- candidate physical XTEST release timestamp preceded candidate handback16/16;
- drain p95 5.966887 ms; max 6.080207 ms;
- NO_EFFECT receipt0/4, completed handback0/4, timeout4/4;
- exact PTY byte, focus readback and helper/XTerm exit gates all pass.

## Integrity failure

The frozen decision gate also requires terminal global X key UP for all36 cases. The executed harness recorded XTEST release+sync but did not independently sample the X server keymap at terminal. Therefore terminal global key-UP evidence is 0/36, not 36/36.

Disposition: `FAIL_INTEGRITY_TERMINAL_KEY_STATE_UNOBSERVED`.

The otherwise-passing numeric result must not be promoted to scientific PASS. A fresh successor may change only this instrumentation boundary by sampling X server keymap state after terminal; it must not reuse/pool A3 rows or change semantic timing/deadline gates.

## Scope

Private same-host Xvfb/XTerm/XTEST only. No model/provider/network/user desktop/MAP01/shared runtime.
