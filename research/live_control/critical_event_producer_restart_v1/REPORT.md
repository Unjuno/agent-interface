# Producer pending-event restart durability — formal result

Task `CRITICAL-EVENT-PRODUCER-RESTART-20260917-001`, Issue #708.

## Decision

**`PASS_PRODUCER_RESTART_DURABILITY_SCOPED`**.

One source-first frozen formal invocation produced 18/18 first outcomes: 3 scenarios × 2 storage arms × 3 repetitions. No retry, replacement, extension or tuning.

## Result

- `kill_after_pending_commit`: SQLite durable pending recovery **3/3** with exact session/seq/id/content digest; volatile recovery **0/3**.
- `kill_before_pending_commit`: recovered pending E4 **0/6** across both arms. No pre-commit phantom recovery.
- `clear_then_restart`: post-clear pending resurrection **0/6**; consumer remains exactly `[E2,E3,E4]` and E4 occurs exactly once in **6/6**.
- The capacity-release path retains the predecessor semantics: first ACK is `ACK_APPLIED`; exact lost-response retry is `ACK_ALREADY_APPLIED`; no additional event is removed.
- Every formal kill receipt records actual subprocess SIGKILL return `-9`.

The manipulated factor is only storage durability of the already-established single producer pending slot. Consumer capacity/backpressure and ACK replay semantics remain fixed.

## Integrity

Prefreeze source was reconstructed from GitHub text chunks and SHA-bound before formal. Postformal source hash recheck passes. Frozen tests re-pass 6/6. Frozen audit returns zero errors. Eight mutations of the actual formal result are rejected: durable loss, false volatile survival, precommit phantom, post-clear resurrection, duplicate E4, ACK regression, wrong kill receipt, and missing row.

Formal result SHA-256 `af2780fcc7575ae85d972d7da7e645dfe117070069659cc61b702183f5b2c9c5`. Audit SHA-256 `c104a067c683829112d1281c4c905ffe37366797c91e2688acedca06f245d399`.

## Interpretation / boundary

This transfers the process-restart durability pattern already seen in #214 to the specific #702 queue-level producer pending-event contract. A committed pending event survives producer SIGKILL/restart; an uncommitted event is not invented; a durably cleared pending event does not resurrect after restart.

This is trusted-local SQLite (`DELETE`, `synchronous=FULL`, explicit transaction) under process termination. It is not evidence for power-loss/storage-controller durability, distributed delivery, multiple pending events, unbounded producer rates, peer authentication, real watcher rates, planner latency or production sizing.
