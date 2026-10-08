# Issue #6079 — conditional parallax T0 result

**Disposition: `PASS_CONDITIONAL_IDENTIFIABILITY_SCOPED`.** Under the frozen synthetic pinhole-raster and rigid-landmark assumptions, a verified lateral-translation probe distinguished all three rigid-approach versus screen-space-overlay pairs. The three zero-motion sham pairs and three noncontact world-sprite pairs with the same visible trajectory remained byte-identical and correctly returned `UNKNOWN`. The candidate produced 3 `DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS` and 6 `UNKNOWN`; it made no contact, safety, or authority assertion.

The independent auditor found zero base errors and rejected all four frozen mutation controls: altered probe receipt, swapped truth label, sham mislabeled as movement, and one-frame pixel alteration. Raw inputs, truth sidecar, candidate/auditor outputs, stdout/stderr, frozen source, and their identities are retained in this directory. The one-shot candidate and auditor command lines are in `FREEZE.json`; exit counts and output digests are in `RUN.json`.

## Reproducibility and deviations

- Allocation: `CONDITIONAL-PARALLAX-6079-T0-20261003-01`; source and input were frozen against main `664f61e24b52fa2f955c486a6c714ca59629f6d9` before either formal invocation. Candidate and auditor each ran once, with no formal retries or threshold changes.
- Runtime: CPython 3.14.5, macOS Darwin 25.6.0, arm64, standard library only. Host CPU only; #6079 permits this fallback when no uncontested container is available. No container, model, network, GUI, game, OS input, GPU, or shared runtime was touched.
- Candidate start time was not captured because the pre-run timestamp command used a `date` option unsupported by macOS and failed before the candidate command. The first successful post-candidate UTC sample was `2026-10-02T16:53:37Z`; no duration is inferred. This telemetry omission does not affect the frozen input/output or audit gates.
- Construction-only failures and their repairs are retained in `CONSTRUCTION_LOG.md`; all six construction tests and `py_compile` passed before freeze. They are not formal candidate outcomes.
- After formal execution, main advanced to `b7300488efd4d27b874785bd024929c886484048` through `6230c49595` and `b7300488ef`. Both commits add only `research/doom/task_effect_source_boundary_1839_successor_v1/**`, disjoint from this allocation. The recorded experiment base and hashes remain unchanged; delivery was rebased by fast-forwarding the branch to current main after this disjointness check.

## Claim boundary and next step

This establishes only a finite observation distinction in the declared synthetic raster model. It does not identify contact semantics when a noncontact sprite has the same visible world trajectory; that case is observationally indistinguishable in the fixture. It does not establish optical-flow robustness under noise, real camera behavior, sprite semantics, harmful contact, GUI/game behavior, local YIELD benefit, release timing, task effect, safety, product benefit, or MAP01 control. Keep #6079's real-scene transfer and #59 live threat-control allocation separate and unclaimed.

Recommended successor: add realistic rendering/noise and independently sourced trajectories only after a safe, non-live capture corpus and a separately auditable contact-label protocol exist. Preserve this finite result unchanged.
