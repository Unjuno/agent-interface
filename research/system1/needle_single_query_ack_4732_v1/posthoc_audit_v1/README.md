# Post-hoc audit of retained #4732 formal raw

This is a separately authored post-hoc replay, not a replacement for the frozen auditor's STOP and not a preregistered formal result. It did not retrain or edit any frozen file. The existing named Docker volume and raw inputs were mounted read-only.

## Outcome

- Docker regression tests: 2/2 passed, using Python's standard-library `unittest` (the pinned image does not include pytest).
- Independent raw replay: 72/72 arm-arrivals, zero errors; exact input regeneration, worker boundary, updates, adapter/optimizer snapshots, query and full-vector predictions, ACK digests, paired parity, and final volume bytes checked.
- Corruption controls rejected: 5/5.
- Timing gate: query-only acknowledgement p95 <=60 ms for all seeds, but ratio <=0.5 failed for all three seeds. Ratios: 0.823, 1.016, 1.690.
- Post-hoc disposition: `POSTHOC_HOLD_LATENCY_BUDGET`.

The result remains qualified post hoc: the frozen formal allocation disposition is still `STOP_AUDITOR_IMPLEMENTATION_DEFECT`. No treatment-effect or model-quality claim follows.

## Files

- `POSTHOC_AUDIT.json`: per-seed replay and gate results.
- `posthoc_audit.py`: separate wrapper; imports only the frozen auditor's raw-validation/recomputation functions, then computes summaries from their actual nested schema.
- `test_posthoc_audit.py`: regression tests for nested summary fields and the 0.5 gate boundary.
- `COMMANDS.md`: reproducible container commands and image identity.
- `test.stdout.txt`, `audit.stdout.txt`: retained command outputs.
