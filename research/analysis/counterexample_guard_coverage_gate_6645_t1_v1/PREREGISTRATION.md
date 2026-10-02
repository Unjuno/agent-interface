# Issue #6645 T1 — hidden-family coverage-gate challenge

## H / T / D / C / U

**H.** A guard-refinement method restricted to a finite, externally frozen
observable-family contract can detect a hidden safety family that is registered
but absent from the candidate's covered predicates, and must return UNKNOWN
rather than pass an otherwise matching state. A legacy seen-feature-only guard
will falsely admit the paired harmful state. This is a boundary test of the
coverage gate named as the required next rung in Issue #6645, not a rerun of its
earlier T0 candidate/refinement allocation.

**T.** Pure finite JSON fixture, no model, GUI, network, user data, or input.
The independently frozen contract requires `target_freshness`, `app_mode`, and
`modal_occlusion`. The candidate covers the first two only. A hidden harmful
case matches the observed `target_freshness` and `app_mode` values of a valid
control but differs in `modal_occlusion`; the legacy guard ignores coverage,
while the challenged guard checks the external contract before admission.
Additional controls include a known stale-target harmful case, an explicit
unregistered-family label, and contract-complete controls. Candidate and
raw-only auditor run exactly once each in separate network-disabled containers.

**D.** `PASS_COVERAGE_GATE_SCOPED` only if the valid complete-coverage control
admits; the known stale control refuses; the hidden-family case would be
admitted by the legacy comparator but returns UNKNOWN under the challenged
gate; the explicitly unregistered family returns UNKNOWN; and the independent
auditor reconstructs all outcomes from frozen fixture/contract/raw inputs with
zero errors. Any hidden harmful admission by the challenged gate is
`FAIL_FALSE_ADMISSION`; a lost valid complete-coverage control is
`HOLD_OVERCONSERVATIVE`; integrity/audit mismatch is `FAIL_AUDIT`.

**C.** The tested comparator is an intentionally coverage-blind guard, not a
production baseline. A PASS shows that an explicit, complete external family
registry can prevent one registered-but-omitted dimension from silently
generalizing; it does not prove the registry is complete.

**U.** A wholly unknown, uninstrumented safety dimension is not detectable from
the finite fixture alone. No result here proves predicate ontology
completeness, live skill/cache behavior, GUI semantics, safety, distributional
generalization, or performance. Any unenumerated family remains outside the
claim and requires UNKNOWN/fallback by contract.

## Frozen execution constraints

- One candidate invocation and one independent auditor invocation; no retries.
- Pinned cached OrbStack image by digest; network disabled; read-only root;
  dropped capabilities; no-new-privileges; bounded CPU/memory/pids.
- The formal fixture, contract, candidate, auditor, runner, and decision gate
  are immutable once `FREEZE.json` is written.
- Preserve any failed command/output as-is and do not relabel it.
