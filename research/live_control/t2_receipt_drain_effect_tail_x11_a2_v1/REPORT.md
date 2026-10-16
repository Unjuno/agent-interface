# T2 live X11 A2 formal result

Issue #1472. Formal invocation 1; reruns/replacements/tuning 0. Four immutable batches, 16 matched pairs / 32 private-X11 cases.

## Disposition

`HOLD_EFFECT_TAIL_AFTER_ACTUATION_DRAIN`

The actuation-receipt drain closes the tested server-side actuation envelope before handback, but does not close the independently visible application-effect tail.

## Frozen results

- IMMEDIATE_TRANSFER: 16/16 local completions after handback; 16/16 possible physical occupancy after handback; 16/16 independently visible effects after handback; 16/16 correct and terminal released.
- ACTUATION_RECEIPT_DRAIN: 0/16 local completions after handback; 0/16 possible/guaranteed physical occupancy after handback; 16/16 independently visible effects after handback; 16/16 correct and terminal released.
- Drain handback delay: p50 6.3809715 ms; max 8.605675 ms.
- Drain effect tail after handback: p50 1.8678885 ms; range 0.286988–4.002464 ms.
- With app delay 0 ms: effect-tail p50 0.3709475 ms, range 0.286988–0.630798 ms.
- With app delay 3 ms: effect-tail p50 3.4163865 ms, range 3.104979–4.002464 ms.
- Audit PASS; errors [].

## Integrity

FORMAL_RESULT SHA-256 `81abf37ef590c8462208413f878903d2d8396c1b7319a381e7c8bd18d701d491`. Gzip SHA-256 `df612f0a58ab60b543b09a9c017065a57bb65f7aaffde461fee7fe40fcbe2028`. AUDIT SHA-256 `fd4e3d4693958b1b1484b5ac252d933db9b8c853abf579b8049dcc305f65243c`. Batch hashes are retained in FORMAL_SUMMARY.json. Full rows are retained as `FORMAL_RESULT.json.gz.b64` and recover by base64 decode followed by gzip decompression.

## Scope

This is one same-host private X11/Tk F8 fixture. XSync intervals bound the server request path, not application semantic completion. The result does not establish MAP01, cross-backend, human-tempo, token, or general production behavior. It directly rejects treating an actuation completion receipt as an effect-completion receipt in this controlled transfer.

## Successor

A successor should change one factor only: handback waits for an independently typed current-effect/feedback receipt instead of redefining the actuation receipt. It must retain ordinary current-evidence/authority semantics and separately charge the extra effect-wait latency.
