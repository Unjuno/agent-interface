# Issue #4588 synthetic first rung v2 — preregistration

**Version status:** separate allocation after v1 `FAIL_INTEGRITY`; v1 files and
results remain unchanged. v2 changes only the sampling/noise pairing and adds
per-pair corpus assertions; decision rules, scenario labels, noise magnitudes,
sample count and output metrics remain as frozen in the copied v1 source.

## H — Hypotheses

- H1: velocity can distinguish matched action/no-op trajectories that share
  current confidence.
- H2: acceleration can distinguish matched action/no-op trajectories with
  identical current confidence and velocity.
- H3: noise can reduce trajectory-rule performance; causal EWMA may trade false
  executable decisions against missed correct actions.
- H4: NO_OP may avoid unnecessary actions, but any rise in missed ACTIONs is a
  potential stall cost and must be counted explicitly.

## T — Frozen test

Execute `probe.py` once in cached `python:3.12-slim`, with no network, a
read-only source/root, and bounded resources. Generate 16 fixed labeled
scenario families × 128 replicates under clean, ±0.01 and ±0.12 confidence
noise. Each replicate draws one irregular two-interval clock schedule and one
three-sample noise vector, shared across every scenario, making the named
counterfactual pairs matched. All four fixed arms receive the same resulting
rows: CURRENT_ONLY, LEVEL_VELOCITY, LEVEL_VELOCITY_ACCEL, and causal time-aware
EWMA SMOOTHED. No arm is trained or tuned.

The output includes exact confusion/false-action/missed-action/NO_OP metrics
and paired feature/decision agreement counts. Assertions require current-only
level and level+velocity alias equality as appropriate, distinct acceleration
for the second-order pair, causal EWMA prefix invariance, and fail-closed
handling of missing, malformed, stale, and epoch-invalid history.

## D — Decision rule

This can only determine whether the fixed synthetic mechanism merits a
caller-visible shadow study. H1/H2 require the paired features to match exactly
and the intended discriminator to separate the clean pair; aggregate accuracy
or false-executable gains cannot override a substantial loss in correct action
recall. H3/H4 report every false executable, missed action, false NO_OP and
correct NO_OP rate; a lower action count caused by stalling is not a benefit.
Any pairing/assertion failure is `FAIL_INTEGRITY`. A synthetic PASS does not
authorize runtime or live-action promotion.

## C — Controls

New allocation seed `20260928`; common random numbers across all scenario
counterfactuals; same noise, irregular sample intervals, labels, and rules for
all arms; no fitting or future input; no model, GUI, input, or authority. Retain
source and preregistration SHA-256, image ID and raw machine-readable output.

## U — Limits / stop conditions

The corpus is synthetic and deliberately constructed; outcomes do not
establish real confidence calibration, generalization, GUI/task correctness,
human tempo, or efficiency. No threshold changes or rerun after inspecting
results. If v2 integrity controls fail, stop without a v3 replacement in this
allocation.
