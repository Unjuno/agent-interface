# Issue #4588 synthetic first-rung preregistration

Status: frozen before execution. Scope is a deterministic, authority-neutral
mechanism probe; no model fitting, GUI, or runtime integration.

## H — Hypotheses

- H1: temporal confidence features distinguish some fixed-label transitions
  that current confidence alone aliases.
- H2: second difference separates the preregistered action/no-op pair with
  identical current level and velocity.
- H3: confidence noise and irregular intervals can erase or reverse a raw
  acceleration advantage; causal EWMA smoothing may mitigate or worsen this.
- H4: an explicit NO_OP class can reduce unnecessary actions without treating
  missing, stale, or epoch-invalid history as permission to wait or act.

## T — Frozen test

Run `probe.py` in the cached Python 3.12 slim Docker image with networking
disabled and source mounted read-only. The script generates 16 named scenario
families × 128 deterministic replicates under three confidence-noise bounds:
clean (0), mild (±0.01), and stress (±0.12). Each row has two irregular sample
intervals drawn in [0.75, 1.25] seconds. The tested arms are CURRENT_ONLY,
LEVEL_VELOCITY, LEVEL_VELOCITY_ACCEL, and causal time-aware EWMA SMOOTHED.
No rule is trained or tuned from generated outcomes.

The locked action rules/thresholds, templates, random seed, and evaluation
metrics reside in `probe.py`. Metrics include exact accuracy, false executable
rate, action recall, missed actions, false NO_OP on an actionable case, correct
NO_OP rate, unnecessary actions, and full confusion counts. A unit-level
assertion verifies the acceleration alias pair, causal smoothing, and fail-
closed handling of missing history. No outputs confer execution authority.

## D — Decision

This rung can establish only a synthetic mechanism signal or typed HOLD/STOP.
It cannot satisfy Issue #4588's held-out real temporal corpus requirement or
authorize shadow/live transfer. A trajectory arm must not increase false
executable rate relative to CURRENT_ONLY; acceleration must add value beyond
velocity on its exact alias; and noise results must be reported even if they
reverse the clean result. Any failed contract assertion is FAIL_INTEGRITY.

## C — Controls

Labels are declared in frozen templates independently of the tested rules.
All arms receive the same confidence samples, timing, labels, and validity
flags; only their feature representation and frozen rule differ. No fitting,
future samples, action emission, or authority fields are permitted. Invalid,
missing, or epoch-stale history returns YIELD. Raw bytes/source digest and
container/image identity will be retained with the result.

## U — Limits / stop conditions

The corpus is synthetic, small in scenario diversity, and intentionally
constructed to expose feature aliasing. It does not demonstrate real-model
calibration, generalization, GUI perception, task effect, cross-application
transfer, safe input admission, human tempo, or token/cost benefit. A scoped
synthetic PASS is not a promotion gate; it only informs whether a separately
frozen caller-visible shadow study is worth proposing. No favorable tuning or
rerun is allowed after inspecting the result.
