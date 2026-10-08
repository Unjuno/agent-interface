# Formal failure — Issue #5375 T0-a1

**Disposition: `FAIL_METHOD_CAPACITY_CONSERVATION`; hypothesis not evaluated.** This retained failure supersedes any interpretation of the candidate's descriptive backlog numbers as a scientific result.

## Frozen attempt

- Allocation: `circuit-metastability-5375-t0-20261001-a1`.
- Frozen main: `73235730af05375fddf3a9d102d30632e7d43af5`.
- One-shot candidate: 12 case-policy groups, 24 ticks each, 288 raw rows. The exact output is retained in `candidate.jsonl`.
- Frozen raw-only auditor output: `{"errors": [], "groups": 12, "rows": 288}`; raw SHA-256 `52DCB63DE8E9D5807E23902D2CF9E0938A61AFFECEC1C6346297468E3A94146A`.
- No candidate rerun or post-freeze repair was performed.

## Stop reason

The simulator counts ordinary `admitted` work and `safety_service` independently. For non-fault ticks in `breaker` and `no_retry`, it permits `admitted=3` and also reports `safety_service=1`, although total capacity is only 3. Thus the claimed independent mandatory safety capacity is double-counted. The frozen auditor checks each field against capacity separately, but omits the required joint invariant `admitted + safety_service <= service_capacity`. A post-run raw-only diagnostic found 100 violating rows across `breaker` and `no_retry` (50 each), with maximum combined service 4 against capacity 3. This invalidates the policy comparison and the preregistered method gate.

Additionally, the synthetic feedback recurrence grows exponentially in the feedback cases (final reported backlog 7,340,033 at multiplier 1 and 26,150,883,008 at multiplier 2 for `breaker`), showing that the selected unbounded law does not yield a useful bounded recovery-dynamics comparison. These values are raw diagnostics only, not evidence of a real metastable system.

## Interpretation and successor boundary

No scientific conclusion is drawn about verifier cascades, circuit breakers, retry-debt shedding, or safety-path availability. The controls and raw arithmetic audit alone do not overcome the capacity defect. Preserve this failure unchanged. Any continuation must be a new successor allocation with a capacity-conserving service model, explicit queue bounds or justified stability region, and an independent auditor that checks joint capacity and any safety-queue conservation before formal execution. Do not reuse these rows as validation of a repaired candidate.

Docker Desktop was observed Engine-running in its UI, but CLI daemon operations were unresponsive and repository coordination records no shared-container lease. No Docker command launching/mutating containers was performed; this bounded CPU-only attempt does not reserve the shared Docker lane.
