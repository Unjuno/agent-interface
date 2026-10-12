# Issue #8668 T0 A02 report — scoped support for phase refinement

## Result

The independent raw-only audit returns `PASS_METHOD_SCOPED` and `SUPPORT_FOR_PHASE_REFINEMENT_SCOPED` for allocation `PHASE-CONTROL-DELAYS-8668-T0-A02-20261009`. It independently reconstructed all 481 frozen schedules and all four policy outcomes per schedule with zero errors. All five preregistered mutation controls were rejected.

| Policy | False cancellation claims | Unsafe duplicate retries | Safe removals missed in retry-requested subset (114 opportunities) | Safe opportunities preserved overall (228) |
|---|---:|---:|---:|---:|
| Static globally cancelable | 102 | 51 | 0 / 114 | 228 / 228 |
| Static globally uncontrollable | 0 | 0 | 114 / 114 | 0 / 228 |
| Fail-closed | 0 | 0 | 114 / 114 | 0 / 228 |
| Phase-refined | 0 | 0 | 0 / 114 | 228 / 228 |

The differences follow the exact comparator contracts frozen in `design.json`. The cancelable comparator equates cancel-command delivery with operation removal when no effect receipt has arrived. The uncontrollable and fail-closed comparators do not issue cancellation. The phase-refined policy uses the modeled phase and bounded delay and admits a retry only after operation-bound removal confirmation. This supports a phase-refined decision rule for this authored finite plant; it does not establish that all static-label supervisors are unsafe or that any real interface exposes the modeled receipts.

## A01 relation

A01's first `PASS_METHOD_SCOPED` was invalidated as `FAIL_HARNESS`: it applied one canceled plant outcome before branching over policies, and the auditor repeated the same counterfactual mapping. A02 is a fresh allocation and fixes that specific defect by simulating each policy action and its resulting plant separately over the same exogenous schedule. A01's source, first raw, first audit, and correction remain untouched; no A01 candidate or auditor rerun occurred.

## Execution and validation

- Frozen base: `ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385`.
- Freeze/source commit: `6fcc7330c4a7ee4a8e6ce092d684f24da29c0289`.
- Candidate: one invocation, exit 0; 1,364,320-byte raw JSON; stderr empty.
- Auditor: one invocation, exit 0; 1,455-byte audit JSON; stderr empty.
- Retries: 0. Network-deny sandbox loopback boundary had been construction-verified as `EPERM` before freeze. No container, GUI, model, GPU, or application was used.
- Pre-freeze construction tests: 8 passed, including row-for-row candidate/oracle agreement over all 481 schedules. Bytecode compilation and `git diff --check` passed.
- Post-run artifact hashes are in `SHA256SUMS.txt`; exact invocations and statuses are in `EXECUTION_RECORD.json` and `RUN_LOG.md`.

## Limits

This is finite deterministic method evidence only. The phase and delay values are authored, phase observability is assumed, and static policies are explicit comparators. The result does not measure natural race frequency, OS or application cancellation, control/observation latency, GUI task completion, input release behavior on a real backend, product safety, or user benefit. A real-backend transfer still needs independently observable phase/effect receipts and a separate authorized allocation.
