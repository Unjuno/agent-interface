# Issue #7794 comparator semantics diagnostic A04

Allocation: CARBON-WINDOW-7794-COMPARATOR-A04-20261005-01. Successor to A03's immutable STOP record; A03 will not be edited or retried.

## Question and H / T / D / C / U

Does the lexicographically earliest globally feasible assignment used by A02 equal canonical-order serial ASAP on the frozen A02 cases, with a two-job discriminator?

- **H:** The comparators differ on at least one A02 case or on the fixed two-job discriminator.
- **T:** Use exact Git blob identities from A03: input fc8f717c700e248198a5c8387ba9f85f5ea7e05e; candidate 1724b00b63bbf48dbbe253e9a1890728fa66ed65; auditor 8191fe468c443a5c0d4c94558e9f235777e5d93c. The A04 auditor reads formal_a04/candidate.json. Run one candidate then one independent auditor invocation, zero retries. Create and verify formal_a04/ before either invocation.
- **D:** PASS_DIAGNOSTIC_SCOPED only if the auditor reconstructs every candidate row and observes a comparator difference on at least one case, including the discriminator. NO_DIFFERENCE_SCOPED if every row agrees. FAIL_AUDIT on any disagreement or omitted case; no rerun.
- **C:** The preferred OrbStack container could not access local containerd blobs: image inspect/list/pull each failed with operation not supported. No alternate runtime/context was available. Explicit native macOS stdlib CPU-only fallback, not a container PASS. No shared daemon repair/prune/restart.
- **U:** Finite synthetic comparator semantics only. No live schedule, emissions, energy, CO2, runtime-performance, or user-effect claim.

## Frozen execution

- Base main: 7e79b4d5fa02d4877f5c53c7f6f234f181e7a5cd.
- Predecessor: A03 branch research/carbon-window-7794-comparator-a03-20261005, PR #8180, terminal STOP_INFRA_CANDIDATE_OUTPUT_PATH; preserve first outcome.
- Package path: research/analysis/carbon_window_7794_comparator_a04_20261005/.
- No network/model/GUI/external side effect. Input and candidate retain A03 Git blob identities; auditor changes only its output path. The API fetch normalizes line endings, so local SHA-256 records exact bytes executed and is not represented as A03's byte hash.
- Construction unit tests are pre-freeze setup checks and do not count as candidate/auditor invocations.
- Formal invocation counts at freeze: candidate 0, auditor 0, retries 0.
