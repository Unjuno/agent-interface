# Issue #8004 — joint unitization/linkage construction A01

**Disposition: PASS_CONSTRUCTION_ONLY; Issue #8004 T0 method gate: HOLD.**
This deliberately authored one-opportunity factorial fixture shows that the
joint combination of a boundary alternative and a record-link alternative can
change a linked capture history when either one-factor change alone does not.
It is an existence/construction demonstration, not a useful ascertainment
estimator, a calibrated uncertainty model, or evidence about repository traces.

## H / T / D / C / U

- **H:** In at least one finite oracle-known fixture, joint boundary/linkage
  uncertainty changes a cross-channel conclusion when either one-factor
  sensitivity does not; unresolved cases should remain `UNIDENTIFIED`.
- **T:** Enumerate the full 2×2 Cartesian product of two authored temporal
  segment alternatives and two linkage-key alternatives. Reconstruct every row
  independently from the raw fixture; include a clean linked control, an
  all-channel-missing denominator control, and mutations of the joint cell and
  assignment denominator.
- **D:** Construction gate passes only if the one-factor cells agree with the
  baseline, the joint cell differs, the complete four-row assignment space is
  preserved, the clean control links, the missed opportunity stays represented,
  and the independent raw-fixture auditor catches both mutations. All conditions
  passed in the retained host run.
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
linked. The method returned `UNIDENTIFIED`. The independent auditor reconstructed
all 4/4 assignment rows with zero errors. The clean control linked, and the
oracle-known opportunity missed by all channels remained in the denominator.
Mutations that changed the joint cell or removed an assignment row were rejected.

The narrowly defined construction gate passed 3/3 tests in both normal and
optimized Python. This is not the full Issue D gate: the issue requires a richer
multi-channel finite simulator, separately varied detection truth/error,
split/merge and false/missed-link controls, and an independent oracle over all
latent opportunities. Accordingly full T0 remains HOLD and `H_PASS_SCOPED` is
not claimed.

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
