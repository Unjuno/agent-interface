# Issue #6684 T0 preregistration

## H / T / D / C / U

- **H:** In a frozen common-mode coordinate-translation family, a relative-coordinate abstraction will reduce conservative `UNKNOWN_REOBSERVE` decisions versus independent BOX intervals while producing zero false `ADMIT` decisions against exhaustive concrete states. On independent target/action frame-error controls it will show no admission advantage.
- **T:** Enumerate the nine deterministic cases in `design.json`. Each is a small integer 2-D grid with finite scale/shift/error domains, immutable intended identity, adjacent forbidden hitbox, frame and epoch. Candidate computes BOX and shared-variable relative bounds; an independently written auditor enumerates every concrete assignment, reconstructs hit/collateral outcomes, checks candidate bounds contain the exact set, and audits controls. One local candidate process and one separate independent auditor process; no retry, network, model, GUI or OS input.
- **D:** `PASS_METHOD_SCOPED` iff (1) exhaustive oracle and candidate audit agree on all represented states; (2) relational admits every frozen safe common-mode case that BOX conservatively refuses, with no false admissions anywhere; (3) classifications are identical for the independent-error controls; (4) unsafe scale-boundary, adjacent-collateral and large independent-measurement-error controls do not admit; and (5) identity, frame, epoch, units, contradictory bounds and relation-sign mutations fail closed or are independently rejected. Any false admission is `FAIL_UNSOUND`; zero scoped gain or a better/equal BOX is `FAIL_NO_GAIN`; incomplete enumeration/audit is `HOLD`.
- **C:** Explicit finite joint hypotheses may be simpler; a box may be equally precise on realistic bounded actions; hand-authored common-mode labels may encode the favorable result. No generic abstract-interpretation or runtime-complexity claim.
- **U:** This is an authored integer geometry model only. It does not test rendering, DPI, hit testing, target identity detection, GUI effects, action authority, or actual coordinate-calibration error. Numerical relation never replaces freshness, focus, lease, release, or independent effect verification.

## Decision details frozen before execution

- Coordinates are integer pixels; rectangle edges are closed and points on the boundary count as inside.
- Concrete state is a Cartesian assignment of each listed integer scale, each independent frame-shift variable, and every target/action/forbidden-object x/y error. Equal `shift_var` names mean the same realized translation; unequal names are independently chosen.
- Intended-target hit requires both absolute relative-coordinate components to be within target half-size. Forbidden-object contact occurs when both components are within its half-size. Safe means hit the intended target and avoid forbidden contact in **every** concrete state.
- `BOX` independently combines each object's screen-coordinate intervals, deliberately discarding common-variable identity. `RELATIONAL` retains exact shared shift-variable cancellation and enumerates the finite scale values when bounding target-action and action-forbidden differences. Both must be sound over-approximations; admission requires the whole abstract difference set to satisfy the corresponding rectangle predicates.
- `INDEPENDENT_SAFE_NO_GAIN`, `INDEPENDENT_UNSAFE_NO_GAIN`, and `INDEPENDENT_FRAME_TRANSLATION_NO_GAIN` are the entire independent-error family. BOX and RELATIONAL must agree on all three; do not count independent-family outcomes as common-mode gain.
- Maximum enumerated concrete assignments per case: 100,000. This is a construction-budget gate, not an inferential sample-size claim.
- One candidate invocation, one auditor invocation, zero retries. If an output, hash, or audit fails, retain it; do not rerun this allocation.

The finite-grid relational-domain analogy is motivated by abstract interpretation and difference/octagon relational bounds, not evidence about GUI behavior: Cousot & Cousot, POPL 1977, https://doi.org/10.1145/512950.512973; Miné, *The Octagon Abstract Domain*, 2006, https://doi.org/10.1007/s10990-006-8609-1.
