# Formal allocation stop — no collection started

Disposition: `STOP_SETUP_OR_INFRA` before the formal invocation. Scientific
rows produced: **0**. The one-shot formal runner was not invoked; no freeze
file, invocation guard, or raw formal output was created. This record does not
replace or relabel any construction evidence.

## H / question

Can the current headless OrbStack ViZDoom/Freedoom MAP01 setup support the
predeclared #3453 live `ASYNC_SPECTATOR` phase allocation without changing the
clock/phase process the allocation intends to measure?

## T / checks performed

- Reconciled GitHub Issue #3453 and PR #3474 review comments immediately
  before collection. The issue requires continuously advancing async
  sessions; an independent review explicitly says a separate-thread
  `advance_action(1)` call is an advancement intervention and requires either
  accepted scope or a passive clock witness before formal freeze.
- Existing excluded diagnostics found passive reads static at tic 1; a single
  startup step advanced only to tic 3, after which reads again stayed static.
  Construction-07 obtained progress by continuously calling
  `advance_action(1)` with an empty button list from another thread.
- Rechecked current source branch and environment artifacts. No
  `FREEZE.json`, formal invocation guard, or formal `raw.jsonl` exists.

## D / decision

At the time of this stop, the candidate image was ViZDoom 1.2.3 and its
headless Python-visible clock remained static without continuous
`advance_action(1)` calls. Later additive construction runs using 1.3.0 and the
normal visible MAP01 configuration found the same stale tic through passive
waits, followed by a large tic catch-up after an action refresh. The exact
scorer returned first-attempt coherent from that cached tic in 3/3 fresh
sessions. See `../CLOCK_WITNESS_RECONCILIATION.md` for the follow-up evidence.

The formal schedule remains unstarted: neither that stale getter snapshot nor
the post-wait catch-up independently brackets the live phase at scorer getters.
The existing driver runner's continuous `advance_action(1)` path is still an
intervention and cannot be relabeled as a passive phase measurement. This is a
scope/measurement HOLD recorded before freeze, not a measured scorer failure,
not a ViZDoom defect finding, and not a formal result.

## C / scope

This stop applies to the current headless runner design and the proposed
passive-async phase claim. It does not invalidate the separately audited
construction instrumentation result, and no construction rows are pooled
with formal data.

## U / next gate

Before a new freeze, either demonstrate and independently audit positive
clock progress in `ASYNC_SPECTATOR` without calling an advancement API during
the measured session, or obtain explicit issue-level acceptance for a
clock-driven fixture and narrow the estimand accordingly. Preserve all
construction artifacts. Any new formal invocation must have a new reviewed
freeze and must still be one-shot.

## Frozen-environment preparation artifacts

These files were captured while preparing, before any game session or formal
row started. They are not a successful formal build result. Docker image build
log SHA-256: `6919087b6560a37c357e04d7608de126a649deb7680eb25fb5fd32ab021ebe5`;
the image resolved to `sha256:64adb4cb546e5bdf672bc031b4c7328aec05dbb60c398e741512f43686ee4ce5`.
This image ID alone does not authorize or constitute the formal allocation.
