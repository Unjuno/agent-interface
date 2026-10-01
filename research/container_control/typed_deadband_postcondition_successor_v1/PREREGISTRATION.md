# Typed deadband/postcondition successor v1 — preregistration

Issue: #2017
Branch: research/typed-deadband-postcondition-successor-v1
Base: main at branch creation time

## Status

FROZEN PREREGISTRATION / NO SCIENTIFIC RESULT

This file defines the next experiment. It does not modify prior evidence and does not claim a container or X11 result.

## Question

Does a task-relative deadband/postcondition cancel locally counterproductive bounded recovery before overshoot while preserving the existing stale-authority and terminal-release gates?

## Arms

- COAST: no local input during planner wait.
- RECOVERY_BASELINE: existing direction plus source-displacement guard, without a task-relative deadband.
- RECOVERY_DEADBAND: the same guard plus typed deadband/postcondition cancellation.

## Fixed conditions

Use the existing rendered Tk/X11 fixture, same planner wait, input budget, drift schedule, resolution, observation path, scorer separation, pair schedule, and correctness gates as the retained v3 mechanics study. Execute in an isolated Linux/Xvfb container. Use a fresh experiment identity and no retry after the first preregistered outcome.

## Required exposures

The retained block must contain at least one natural deadband-entry cancellation and at least one natural stale-guard invalidation. If either exposure does not occur, disposition is HOLD_NO_REQUIRED_EXPOSURE, not PASS.

## Measurements

Retain exact rendered frames, typed observations, controller receipts, key-down/up events, scorer-only stream, held-input occupancy, cancellation timing, guard invalidation-to-release timing, unsafe exposure, stale repress count, balanced key events, terminal input state, visual decoder error, source hashes, container manifest, raw manifest, and independent audit output.

## PASS boundary

A PASS is scoped to rendered Tk/X11 mechanics only and requires:

- every retained v3 gate;
- required deadband and stale-guard exposures;
- zero stale repress before planner return;
- balanced app-side key events;
- empty terminal input state;
- raw-manifest and independent-audit agreement;
- recovery-deadband not worse than the declared paired baseline on the preregistered primary metric.

A finite-sample zero harmful tail is not a safety guarantee and does not establish DOOM, GUI-general, human-tempo, model, token, latency, or production claims.

## Stop rules

Stop and retain the first outcome if source provenance, receipt lineage, scorer separation, decision cardinality, release verification, or raw-manifest verification fails. Preserve failed and incomplete outcomes; do not overwrite or retry them.

## Planned integration

Add the runner, immutable raw result directory, audit script, report, and research-index entry only after the preregistered run and independent audit. Merge through a PR.