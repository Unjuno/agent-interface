# Issue #6315 — finite-trace edge-count and deadline discriminator (T0)

## H / T / D / C / U

**H.** On a finite, explicitly covered typed source trace, the candidate projection plus declared evidence can (a) preserve untimed stutter-invariant claims when complete relevant valuations agree, (b) reject a projection changing exact critical-edge count or a bounded sampled-event deadline, and (c) return `UNKNOWN` when completeness, required values, timestamps, or clock mapping are absent. It must distinguish a trace-property comparison from what a receiver can infer about an incompletely observed source.

**T0.** Standard-library-only synthetic construction. Compare identity, adjacent full-relevant-valuation stutter collapse, latest-state-only, and explicit critical-edge retention. A frozen fixture has six cases: benign complete untimed stutter; two distinct same-type edge occurrences reduced to one; a fully timestamped deadline edge witness removed while later equal-valued state remains; missing timestamp; missing interval coverage; and a preserving timed control retaining the within-deadline witness. The independent auditor receives only frozen fixture/property definitions plus candidate raw output; it independently recomputes source and projection truth, coverage-qualified epistemic verdict, occurrence count, deadline witness, and mapping. Construction mutations target occurrence retention, deadline-edge retention, duplicate case/mode evidence, and kept-index mapping.

## Frozen meanings and gates

- One source clock domain, integer milliseconds, monotonic, inclusive deadline `t_ms <= deadline_ms`.
- Event count is by unique occurrence ID for event type `alarm` over fully covered closed interval `[0, 10]`; duplicate occurrence IDs count once and malformed/conflicting duplicates are invalid.
- Deadline property is an observed `ready` rising edge by `t_ms <= 10` on the complete sampled trace. This makes no continuous-time/inter-sample claim.
- Source truth and projected truth are recomputed separately. `PRESERVED` means source truth is established, projected truth is established and equal, with a valid replayable source-index mapping. `NOT_PRESERVED` means source truth is established and projection is false or lacks required evidence. `UNKNOWN` applies when source truth itself cannot be established because source coverage, required semantics, timestamps, or clock mapping are absent; unknown is never converted to false.
- Source epistemic truth is `UNKNOWN` unless source coverage and required evidence are complete. This fixture's explicit `unobserved` interval demonstrates that boundary.
- `PASS_METHOD_SCOPED` requires all six expected cases, correct positive/negative/unknown classes, replayable witnesses, and all four construction mutation rejections. Otherwise FAIL/HOLD; no favorable relabeling.

## Isolation, allocation, and stop rules

New allocation: `TEMPORAL-COALESCING-6315-T0-20261002-01`; additive path is this directory. Candidate completed once (exit 0) and auditor-v1 completed once (exit 0). Post-run evaluation found an auditor-v1 defect: it certified `PRESERVED` when projection evidence was unavailable and used projection false as enough to establish source truth under incomplete coverage. Candidate replay is forbidden. Preserve raw v1 output; any auditor correction is an audit-only successor allocation with separate raw artifacts.

## Scope boundary

No live GUI/capture, GUI coverage, continuous-time truth, backend state, model, action authority, user data, or human-tempo evidence. Finite synthetic method evidence only; the independent implementation can itself contain defects.
