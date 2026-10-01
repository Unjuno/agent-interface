# Issue #16 T4 — execution/audit STOP

The one-shot frozen candidate ran on the host and exited 0, emitting 12 JSONL rows. The frozen independent auditor then exited 1 before producing an audit result:

```text
KeyError: 'record_id'
```

The `compensator_failure_control` row was appended without a `record_id`; the frozen auditor indexed that field unconditionally. The plan also incorrectly expected 10 rows, while its own frozen coverage set has 12 (11 strict schedule prefixes plus one compensation-failure control). This is `STOP_AUDIT_SCHEMA_AND_PLAN_COUNT`, not a PASS. No source, raw row, or prior Issue #16 result was edited; neither runner nor frozen auditor was rerun.

The raw SHA-256 is `4373a75c846166309a183887a83937b3f2f9c7e948915eda42f9151495ee0204`. Candidate and frozen-auditor hashes remain those in `PLAN.md`. A separate post-hoc reconstruction audit is retained as supplemental diagnosis only; it does not retroactively satisfy the frozen gate or authorize merging as a scientific PASS.

Execution boundary: base `7fcf30f37e122bc3fce7ab893aebd9bfa4a864a8`, frozen source commit `2a21ca8d10b4834e98e854730e7b19fef1c0342c`, CPython 3.14.5 host, one candidate invocation and one frozen-auditor invocation. No Docker/OrbStack call, GUI, model, network, or external effect. The shared container slot was not assigned to this lane in #5085.
