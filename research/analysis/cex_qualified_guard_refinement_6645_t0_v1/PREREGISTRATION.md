# Issue #6645 — counterexample-qualified guard refinement T0

## Status

H/T/D/C/U frozen for a deterministic, synthetic, no-model accounting/method
experiment. The finite fixture's oracle is stipulated; it is not a complete GUI
semantics oracle. Formal execution is restricted to WSLc, offline, CPU-only,
with the digest-pinned cached Python image and one candidate plus one separate
raw-only audit invocation. Until a named WSLc host/allocation is available,
host-side test runs are construction only and must not be relabeled formal.

## Collision and predecessor boundary

Issue #4260 completed its one-shot guarded-inline-cache lifecycle check: warm
specialization/deoptimization was scoped to one Xvfb/Tk operation and did not
include automatic guard synthesis. Issue #5504 completed its finite CEGAR
checks, while later hidden-family evidence showed false PASS on all five
held-out predicate families. T0 here therefore tests only whether a closed,
declared observable predicate vocabulary can safely distinguish a frozen
counterexample family and detects observational aliases as UNKNOWN. It makes
no generalization or ontology-completeness claim. No matching open PR or
branch was found on 2026-10-02; refresh before formal allocation.

## H / T / D / C / U

- **H:** Given a finite declared observable vocabulary and independent replay
  classification, counterexample-qualified refinement can exclude every
  distinguishable harmful state, preserve distinguishable valid controls,
  invalidate all dependent sibling specializations, and return UNKNOWN for a
  safe/harmful observational alias—without adding authority or replaying task
  input.
- **T0:** Execute the finite fixture in `fixture.json`. Compare unchanged guard,
  invalidate-all/fallback, exact-state blacklist, candidate refined guard, and
  oracle-minimal diagnostic. Include real guard miss, spurious/unresolved/out-
  of-scope traces, stale generation, two incomparable refinements, a valid rare
  control, a hidden-family safe/harmful alias under identical allowed
  observations, shared-predicate sibling caches, unavailable fallback, and
  corruption controls. Candidate and auditor are separate implementations.
- **D:** `PASS_METHOD_SCOPED` only when the auditor reconstructs every raw row;
  only independent `REAL_GUARD_MISS` evidence causes refinement; every
  distinguishable harmful control is refused; every distinguishable valid
  control remains admitted; every aliased safe/harmful class is `UNKNOWN`;
  predicate-dependent siblings invalidate; the generic path receives no new
  authority and no task input is replayed; all planted mutations are rejected.
  Otherwise `FAIL_METHOD` for unsafe admission, self-certification, unjustified
  overfit, missed invalidation or fallback authority escape; `HOLD_UNIDENTIFIABLE`
  for an unresolved observation alias; `HOLD_RESOURCE` before formal start if
  WSLc assignment/image prerequisites are absent.
- **C:** Exact finite predicates and a correct generic path may make synthesis
  unnecessary. Conservative invalidate-all can be preferable when provenance
  or observability is weak. Predicate minimization is only relative to this
  frozen finite vocabulary.
- **U:** Oracle independence, closed-world predicate coverage, real cache
  dependencies and fixture representativeness are assumed. No live GUI,
  runtime safety, model/token/latency benefit, cross-app transfer or production
  completeness is established.

## Frozen execution and interpretation

No GUI, model, user input, network, GPU, credential, application artifact or
external side effect. The candidate may inspect only stipulated public
observations and replay classifications; it must not use hidden truth labels to
select predicates. Predicate alternatives tied under the frozen objective are
all retained. No tie-break using hidden oracle labels.

At most one formal candidate and, only after candidate exit 0, one independent
auditor invocation; retries/replacements/post-result tuning = 0. No Docker or
OrbStack substitute for WSLc. Requested resource limits do not prove kernel
enforcement. Preserve every construction failure separately from formal
outcomes.
