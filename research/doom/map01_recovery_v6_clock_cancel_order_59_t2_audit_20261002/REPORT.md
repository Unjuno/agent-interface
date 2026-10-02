# v6 clock/cancel order — independent audit of retained T1 trace

Issue [#6236](https://github.com/Unjuno/agent-interface/issues/6236), successor audit to #6232/#6228 and parent #59. No candidate, executor, or game code was executed in this audit allocation.

## Result

**PASS_CLOCK_DELAY_EXTENDS_WITHIN_LEASE_SCOPED.** One independent raw-only audit invocation; candidate invocations 0; retries 0; errors 0. It independently verifies that the frozen v6 runner source samples the planner-end clock before issuing fallback cancel and that the retained candidate trace meets every preregistered A/B/C timing and event gate.

- **A, clock then cancel, lease remains valid:** timer occurred 601.5276 ms after start; delayed clock returned 400.1232 ms after timer; cancel was requested 400.1587 ms after timer; verified release followed the timer by 400.1976 ms and followed cancel by 0.0389 ms. Cancel matched, the fake observed it, release was verified, and terminal status was `completed`.
- **B, lease expires while clock is delayed:** lease expired/released 1,507.6524 ms after start (7.6524 ms after the 1,500 ms deadline), before clock returned 1,600.5179 ms after timer. No cancel was observed; post-return cancel was unmatched; verified terminal status was `expired`.
- **C, cancel before clock delay:** verified release followed timer by 0.0562 ms and cancel request by 0.0390 ms. Cancel matched and was observed before clock return.
- Independently recomputed A-minus-C release-after-timer difference: **400.1414 ms**, exceeding the preregistered 300 ms margin.

The earlier T1 report's unit correction is confirmed: C's 56,200 ns is 0.0562 ms, not 56.2 ms. T1's first auditor path failure remains intact; this result comes from the separately preregistered #6236 audit-only successor, not a retry of #6232.

## Frozen identity and method

Raw source: commit `05e050fdcdf179d9559324bcbc72cfdc82b77a2a`, path `research/doom/map01_recovery_v6_clock_cancel_order_59_t1_20261002/raw_trace.json`, SHA-256 `f487b79a16920cc584167722098ea446b51c81f8e0788caee1b7bdd147b22c67`.

The independent auditor read those bytes directly from the Git object and re-read the v6 runner, executor-v10, and Lease from base `673763554192ae26636e07d5a48f03b3cd7fb044`. All three Git blobs, SHA-256 values and byte counts matched the raw source manifest. Source-order and all preregistered configuration, timing, cancellation, terminal, and release predicates passed.

Commands:

```powershell
python research/doom/map01_recovery_v6_clock_cancel_order_59_t2_audit_20261002/audit_retained_trace.py --construct-only
python research/doom/map01_recovery_v6_clock_cancel_order_59_t2_audit_20261002/audit_retained_trace.py
```

The first command verified the pinned raw/source identities only. The second and final command performed the single independent audit. Candidate raw snapshot and machine-readable calculations are retained alongside the frozen audit source.

## Scope and limits

This supports only a deterministic timing effect in one cooperative fake backend running against the exact executor-v10/Lease Git objects, plus a source-order check. The orchestration simulates the synchronous clock-response delay; it does not run the complete v6 `_run_arm`, interprocess transport, MAP01, a live GUI, or actual held-key input. It does not measure natural RPC-delay frequency and makes no gameplay, safety, survival, task-efficacy, or product claim. The Docker engine/shared slot was unavailable, but a container is not required for this read-only posthoc raw audit; no engine was touched.

## Files

- `audit_retained_trace.py` — frozen independent raw-only auditor.
- `candidate_raw_snapshot.json` — byte-identical snapshot of #6232 raw trace from the pinned commit.
- `independent_audit.json` — recomputed predicates and PASS disposition.
- `SHA256SUMS` — package integrity manifest.
