# Issue #3212 two-container orchestrator restart — 2026-09-20

Additive restart experiment; prior records remain unchanged.

## H/T/D/C/U

- H: A receipt persisted across an orchestrator/container restart must not regain input authority when the receipt-owning browser resource is gone.
- T: Container A ran the real Chromium/Xvfb receipt allocation with `--network none` and wrote the receipt summary to a shared volume. Container A then exited. Container B, also `--network none` and using the same image, loaded the persisted receipt from the shared volume and evaluated replay admission with no owner browser process present.
- D: Container B loaded the receipt successfully (`receipt_loaded=true`), observed `browser_process_present=false`, and returned `admitted=false`, `dispatch=false`, `effect=false`, reason `owner_container_exited`. Container A produced distinct XIDs `4194307` and `12582915`; no external network or model call was used.
- C: `PASS_CHROMIUM_ORCHESTRATOR_RESTART_INVALIDATION_FAIL_CLOSED_SCOPED`. This proves persisted-receipt denial after owner-container exit for this fixture. It does not prove graceful state restoration or a live orchestrator that recreates a valid browser resource.
- U: Test a graceful orchestrator restart that restores a new browser resource and requires a new generation/receipt before effect; retain any restoration failure as STOP/HOLD.

## Raw result

```json
{"phase":"orchestrator_restart_container_b","receipt_loaded":true,"browser_process_present":false,"admitted":false,"dispatch":false,"effect":false,"reason":"owner_container_exited"}
```
