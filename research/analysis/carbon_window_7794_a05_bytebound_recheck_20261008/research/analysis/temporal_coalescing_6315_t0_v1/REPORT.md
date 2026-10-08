# Issue #6315 — finite-trace edge-count/deadline T0

## Result

Disposition: `PASS_METHOD_SCOPED` for the corrected, finite synthetic evaluator only, with an important retained failure: allocation-01's first independent auditor (`audit.raw.json`) had a decision-logic defect and must be read as `HOLD_AUDIT_IMPLEMENTATION`. The corrected auditor was run once as a separate audit-only successor against the unchanged single candidate raw (`audit-v2.raw.json`); it reports 14/14 case-mode rows and rejects 4/4 mutation controls. Candidate execution: one invocation, exit 0. Auditor v1: one invocation, exit 0. Corrected auditor: one invocation, exit 0. No retries or candidate reruns.

| Frozen condition | Scoped result |
|---|---|
| Harmless complete untimed stutter | `PRESERVED` under exact-full valuation collapse and latest-state-only |
| Two unique `alarm` occurrence IDs, projection drops both | Source count 2, projection count 0; `NOT_PRESERVED` |
| Deadline `ready` rising edge at t=9, projection loses edge and only later false remains | Source true, projection false; `NOT_PRESERVED` |
| Missing required timestamp | `UNKNOWN` |
| Incomplete source interval coverage | Source epistemic truth `UNKNOWN`; verdict `UNKNOWN` |
| Critical-edge-retaining controls | `PRESERVED` for both count and deadline fixtures |
| Mutations: edge retention, deadline edge, duplicated case/mode, index mapping | 4/4 rejected |

These are authored deterministic fixture outcomes, not GUI prevalence or deployment metrics. Retaining typed critical edges is sufficient for these tested properties/cases; a general certificate mechanism's advantage over that simple rule was not demonstrated.

## Reproducibility and audit

Exact pinned-image identities, network/resource limits, argv, exits, empty stdout/stderr, candidate/auditor raw, the original flawed audit, corrected audit, and their digests are retained in `FREEZE.json`, `results/formal-01/RUN.md`, and `results/formal-01/SHA256SUMS`. Construction tests: 3/3 pass. The candidate never received auditor source. The independent auditor did not receive candidate source. The defect discovered after v1 was not concealed or used to overwrite v1; candidate was not replayed.

## Limits

This evaluates explicitly typed finite traces under one source-clock domain, inclusive integer-millisecond deadlines, unique event occurrence IDs, and explicit coverage labels. It proves no continuous-time property between samples; no live capture completeness, hidden application/backend state, GUI task effect, model behavior, action authority, privacy/safety rate, or product benefit. An independent implementation can still share conceptual errors with the candidate specification.
