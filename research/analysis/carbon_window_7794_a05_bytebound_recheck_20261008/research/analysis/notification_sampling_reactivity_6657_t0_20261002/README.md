# Issue #6657 T0 — notification-conditioned sampling reactivity

This is a finite method experiment for separating clock-time exposure from
inspection/check-in-conditioned exposure when the inspection schedule reacts to
notifications. It uses a scripted trace only; it does not measure people or
notification effects in deployed software.

## Reproduction

From the repository root, run the construction suite:

```sh
python3 -B -m unittest discover -s research/analysis/notification_sampling_reactivity_6657_t0_20261002 -p 'test_*.py' -v
```

The formal frozen invocations are recorded in `FREEZE.json` and
`results/t0-01/RUN_RECORD.json`. Candidate and independent auditor outputs are
immutable; their source, input, and output digests are recorded in
`SHA256SUMS`.

## Scope

The exact tick-weighted clock-time fraction and uniform random-epoch expectation
are known from the fixture. The seeded 12-draw sample is separately reported and
is not required to equal the population expectation. Silent, milestone-reactive,
noisy-status-reactive, and visible-but-nonreactive schedules use the same fixed
base checks. The independent auditor reconstructs time state from half-open
progress intervals rather than importing the candidate.

The execution is native macOS host CPU only (CPython 3.14.5 / arm64). OrbStack
was not used: its current inventory contains active machines for other research
work, and this exact finite method does not require container semantics. No
model, GUI, participant, user data, network, or external effect was used.

## Interpretation boundary

`PASS_METHOD_SCOPED` validates the finite estimator/schedule accounting only.
It does not establish that real people respond to notifications, that a
notification causes a timing change, or that any notification policy improves
oversight. The full human hypothesis remains untested and requires a separately
approved, consented study with independent epoch sampling.
