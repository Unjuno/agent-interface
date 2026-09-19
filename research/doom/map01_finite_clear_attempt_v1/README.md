# Freedoom MAP01 finite ordinary-speed clear attempt

This is the preregistration and evidence contract for Issue #2679. It is an
additive successor/integration allocation; prior MAP01 attempts and failures
remain immutable.

## H/T/D/C/U

- **H:** the integrated Agent Interface path can sustain bounded visual
  observation and OS keyboard/mouse control while asynchronous game time
  continues through model waits, reaching an auditable terminal outcome.
- **T:** run packaged Freedoom 2 `MAP01` in `ASYNC_SPECTATOR` at a target 35
  tics/second through the existing X11 screen-capture and OS-input path. The
  controller sees only screen/audio evidence and may use keyboard/mouse input;
  pause, save-state, automap, object labels, sector labels, hidden pose and
  privileged game state are prohibited.
- **D:** retain raw observations, action and release events, decision/model
  trace, game-tic and wall timestamps, observation age, capture/render rate,
  scorer output, provenance hashes, and synchronized video when available.
- **C:** `PASS_FINITE_CLEAR_SCOPED` requires independently scored actual MAP01
  exit before death/timeout, continuous ordinary-speed execution, bounded input
  and complete provenance. A complete no-exit run is
  `FAIL_FINITE_CLEAR_NO_EXIT`; infrastructure failure is
  `HOLD_INFRASTRUCTURE`.
- **U:** completion, threat robustness, reproducible synchronized video,
  human-speed parity, token efficiency, general gameplay competence and public
  demo readiness remain unknown.

## Frozen boundaries

The allocation must use a fresh additive result namespace under this directory
and must not modify shared runtime semantics or replace any retained
`map01-assistant-feasibility-*`, `map01-overlap-*`, or prior result. The
independent terminal scorer must distinguish exit, death and timeout from
controller-visible evidence and preserve malformed-command rejections.

The actual run is not claimed by this preregistration. Its result, failure, or
infrastructure stop must be added as an immutable sibling artifact before any
promotion or public claim.
