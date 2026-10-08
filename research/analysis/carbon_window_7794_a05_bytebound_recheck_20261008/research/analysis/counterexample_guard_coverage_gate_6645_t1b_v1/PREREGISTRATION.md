# Issue #6645 T1b — isolated coverage-gate counterfactual

## H / T / D / C / U

**H.** Holding the same observation-limited guard fixed, enabling only the
coverage gate changes a hidden harmful state with an omitted required
predicate from ADMIT to UNKNOWN, while leaving a fully covered valid control
ADMIT and a fully covered known harmful control REFUSE. The candidate receives
no oracle labels or hidden modal value.

**T.** Pure finite fixture; candidate-visible inputs and oracle labels are in
separate files. Each row is evaluated by the same candidate function twice;
the only intervention is `coverage_gate_enabled`. The hidden harmful and safe
rows have byte-identical candidate-visible observations and both omit
`modal_occlusion` from covered predicates. The gate checks the frozen external
contract and supported surface family before the same guard evaluates its
covered predicates. Candidate and independent raw-only auditor run once each
in separate network-disabled OrbStack containers.

**D.** `PASS_COVERAGE_GATE_ISOLATED_SCOPED` only if the gate-disabled hidden
harmful arm ADMITs, the gate-enabled arm returns UNKNOWN, the fully covered
valid pair ADMITs in both arms, the fully covered stale-target pair REFUSEs in
both arms, hidden safe/harmful indistinguishable rows receive the same gated
decision, and the independent auditor reconstructs all outputs with zero
errors. A failed gate contrast is `FAIL_NO_GATE_EFFECT`; changed non-gate
decisions are `FAIL_NOT_ISOLATED`; audit discrepancy is `FAIL_AUDIT`.

**C.** This repairs the counterfactual confound found in the merged T1: the
candidate no longer reads the hidden modal field or oracle outcome in either
arm. The no-gate arm differs only by skipping the coverage-eligibility check.

**U.** The frozen external registry is still assumed complete. This test does
not discover unknown-unknowns, establish registry authenticity/completeness in
real systems, or demonstrate live skill/cache, GUI, safety, or performance
behavior. It is synthetic method evidence only.

## Frozen execution constraints

- Allocation `CGCG-6645-T1B-ORB-20261003-01`; one candidate invocation and one
  independent auditor invocation, retries 0.
- Cached pinned OrbStack image by digest, network none, read-only root, dropped
  capabilities, no-new-privileges, bounded CPU/memory/PIDs.
- Freeze every candidate-visible input, contract, oracle, source, test, runner,
  and decision gate before either formal invocation.
- Preserve all first outcomes; no reruns or silent edits.
