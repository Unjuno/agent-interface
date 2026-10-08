# Issue #8004 — joint unitization/linkage construction A01

**Disposition: LOGIC_TOY_ONLY; Issue #8004 T0 method gate: HOLD.**
This deliberately authored one-opportunity factorial truth table illustrates
the logical possibility of an interaction between a boundary choice and a link
choice. Post-run review found that the candidate reads oracle identity and
all-channel-missing truth fields directly from its input. It therefore does
not independently test linkage, ascertainment, or denominator retention. See
`A01_SCOPE_CORRECTION.md`; the original outputs are preserved unchanged.

## H / T / D / C / U

- **H:** In at least one finite oracle-known fixture, joint boundary/linkage
  uncertainty changes a cross-channel conclusion when either one-factor
  sensitivity does not; unresolved cases should remain `UNIDENTIFIED`.
- **T:** Enumerate the full 2×2 Cartesian product of two authored temporal
  segment alternatives and two linkage-key alternatives. Reconstruct every row
  independently from the raw fixture; include a clean linked control, an
  all-channel-missing denominator control, and mutations of the joint cell and
  assignment denominator.
- **D:** The narrow logical truth-table check found that only the joint cell
  differs. This is not an independent method gate: candidate-visible inputs
  contain oracle fields, and no scored population denominator is computed.
- **C:** The result depends on authored alternative spans and linkage keys.
  Stable unique IDs or a different admissible assignment set could eliminate
  the interaction; a sensitivity envelope may be uninformative when ambiguity
  is unconstrained.
- **U:** One deliberately selected opportunity, two channels, one boundary
  alternative, and one link-key alternative; no empirical false-match/miss
  distribution, heterogeneous sensitivity, dependence graph, split/merge
  population, censoring, estimator calibration, human annotation, or live trace.
  The design is authored to expose an interaction, so it is not an unbiased test
  of how often such interactions arise. No production incident count, safety,
  or T0 `PASS_METHOD_SCOPED` claim follows.

## Observed result

The candidate enumerated four assignments. Baseline `(S0,L0)`, segmentation-only
`(S1,L0)`, and linkage-only `(S0,L1)` were unlinked; only joint `(S1,L1)` was
linked. The independent auditor reconstructed all 4/4 rows with zero errors.
However, this verifies only a tiny truth-table implementation: `candidate.py`
reads the truth-backed `channel_b_identity`, and its missing-channel Boolean is
copied from a truth flag. The tests mutate an assignment-row denominator, not
the latent-opportunity denominator. The first output's PASS-like booleans remain
historical artifacts and are not accepted as proof of independent ascertainment.

The 3/3 tests in both Python modes passed for the toy logic only. This does not
meet even the independent-oracle portion of Issue D, much less its full T0 gate.
Full T0 remains HOLD; no construction or hypothesis PASS is claimed.

## Execution and provenance

- Current `main` observed immediately before local construction: `3b60eeedf0dbfe8bfab52175c832600e84f2d6b5`.
- Host: macOS 27.0.1; Python 3.14.5; standard library only.
- Commands: `python3 -m unittest -v test_method`; `python3 -O -m unittest -v test_method`; `python3 candidate.py --fixture fixture.json --output run_candidate.json`; `python3 audit.py --fixture fixture.json --candidate run_candidate.json --output run_audit.json`; `python3 -m py_compile candidate.py audit.py test_method.py`.
- This run was host-side exploratory execution, not a container run and not a
  preregistered formal T0. OrbStack image inspection returned containerd
  `operation not supported`; no image pull, container launch, prune, VM start,
  or daemon change was attempted.
- The fixture/source hashes and observed command/results are recorded in
  `FREEZE.json` and `SHA256SUMS`. The package was built in a standalone
  workspace directory, then added on a dedicated branch and submitted as draft
  PR #8011 for review; it is not merged into `main`.

## Reproduction

Run the commands above from this directory. Outputs are retained as
`run_candidate.json` and `run_audit.json`. No network, model, GUI, user data,
runtime allocation, or shared container was used.
