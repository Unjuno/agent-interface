# T0 formal run — Issue #6338

Allocation `t0-formal-02`; frozen source base `main` SHA `8ff2eddf995e079f7e3a11b87f964734403996fb`; window 2026-10-02 01:26–01:41 UTC. Native Windows 10.0.26200.9457, Python 3.11.9, PowerShell. No model, GPU, WSL, Docker/container, network, or human contact.

## Commands and raw outcome

1. `python -B candidate.py cases.json results/formal-02/candidate.json` — exactly once, exit 0. SHA-256 `EC0FF53CD8AFBE7406692643C720910F351786FD6B475CD9363F87B23523DBB5`.
2. After candidate exit 0, `python -B auditor.py cases.json results/formal-02/candidate.json results/formal-02/audit.json` — exactly once, exit 0. Independent raw-only status `PASS_METHOD_SCOPED`, zero errors. SHA-256 `2F6544E26145785E5BA13A05D0B18072CAC3839B92A8B155660650852ADF3E6B`.

The preceding construction suite ran 14/14 tests; five required planted corruption classes were rejected, plus two added tests for raw parent-edge and independent effect aggregates. Python compilation passed. Construction-only defects were fixed before `t0-formal-02`; no candidate or auditor was run for superseded unspent allocation `t0-formal-01`.

## Findings

| Fixture | Outcome |
|---|---|
| Exogenous simultaneous burst | 3 notices under all policies; 0 parent edges; maximum card chain 1. |
| Two-generation clarification/re-review | Emit-each 3 notices / chain depth 3; duplicate batching also 3 / 3; source-linked 2 / 2. Independent task-effect truth remains 3 in both emit-each and source-linked. Frozen final-event trace span 12 for every policy. |
| Identical duplicates | 3 notices emitted; exact-duplicate batching reduces to 1. |
| Target revision | Two version-specific notices; stale approval rejected. |
| Denial/nonresponse | No extra notices; finite trace span 20. |
| Cross-principal attempt | Unauthorized attempt emits no notice. |
| Urgent hard alert | Both hard alerts preserved under every policy, including duplicate-shaped alerts. |
| Opaque consolidation negative control | Three actionable cards → one opaque card; correct effects 3 → 0. Disposition exactly `CHAIN_REDUCTION_WITH_BURDEN_UNKNOWN_OR_WORSE`. |

## Decision and limitations

`PASS_METHOD_SCOPED`: this deterministic finite ledger distinguishes a common-cause exogenous burst (no source edges) from a two-generation parent-linked chain, and the fixture’s source-linked policy reduces the specified chain’s card count and tail depth without changing its independently scored effect truth. Exact deduplication does not explain that chain reduction. The raw auditor passes all frozen invariants; mutation controls reject missing parent, stale/cross-card approval, hard-alert suppression, cross-principal merge, and mislabeled opaque result.

This is not causal evidence from observed users. Parent links are fixture truth, not proof that an event source caused a real response. `trace_span_to_quiescence` is a deterministic final-event span, not human waiting time. No claim about attention, human burden, Hawkes fit/branching ratio, prevalence, task performance outside the fixture, or product behavior. T1 remains separately consent/privacy gated.
