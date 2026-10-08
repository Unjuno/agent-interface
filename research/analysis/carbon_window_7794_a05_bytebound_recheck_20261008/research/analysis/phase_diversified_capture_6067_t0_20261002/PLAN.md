# Issue #6067 T0 — phase-locked repeated-miss boundary

## Novelty boundary

PR #6093 / Issue #6086 evaluates hazard-shaped schedules under a declared nonuniform onset distribution. This allocation instead isolates the distinct #6067 question: repeated periodic cue phases synchronized against a fixed-period sampler, and whether phase diversity reduces four-consecutive miss probability under an explicit inter-capture-gap cap. It makes no claim about live cue onset distributions or runtime value.

## H / T / D / C / U

- **H:** For periodic cues on a finite phase grid, uniformly selecting a phase-offset cycle from all equal-budget schedules satisfying a frozen maximum-gap bound reduces the worst-phase probability of missing four repeated cue episodes versus a fixed periodic phase, without exceeding that bound.
- **T:** Exact integer interval enumeration. Period `T=12`, four captures/cue repetitions, cue widths `d∈{1,2,3}` slots, 12 possible onset phases, instantaneous captures at integer offsets, and cyclic maximum inter-capture gap `18=1.5T`. Enumerate all `12^4` offset cycles; admit iff every cyclic adjacent gap is ≤18; choose uniformly over the admitted finite schedule family. Compare probability of zero hits over the four repeated cues for each phase. Independent auditor uses base-12 integer decoding rather than candidate product enumeration.
- **D:** `PASS_METHOD_SCOPED` only if independently computed schedule count and all phase-specific miss counts match; every admitted cycle respects gap cap; for each frozen cue width the worst-phase four-miss probability under the diversified family is <1 (the fixed periodic schedule's worst-phase probability). Otherwise FAIL; HOLD if enumeration/audit is incomplete. No schedule is claimed to guarantee detection for every seed/phase.
- **C:** Reliable event subscriptions/latching can remove the visual sampling problem; deterministic phase rotation or a direct phase estimator may outperform random selection. The 1.5T gap cap is an explicit analytic constraint, not a validated application deadline.
- **U:** Idealized integer time, instantaneous capture, stationary periodic cue, finite phase/width family, uniform selection over the admitted schedule cycles, and no capture cost/side effect. No finite result establishes live detection, safety, arbitrary/adversarial timing, or task benefit.

## Allocation

`PHASE-DIVERSIFIED-6067-T0-20261002-01`. Formal source is frozen in `FREEZE.json` before the one official candidate/auditor run. The local test suite is construction validation only. No retry or tuning after freeze.

## Container decision and command

This is exact bounded integer enumeration; platform/runtime behavior is not part of the claim, so container isolation is not methodologically required. Docker Desktop's Linux Engine did not answer recent CLI probes within the configured 10-second window; no container run is claimed. Official commands: `python candidate.py` and `python audit.py` in this directory. `python -m unittest -v test_audit.py` is a separate local integrity check.
