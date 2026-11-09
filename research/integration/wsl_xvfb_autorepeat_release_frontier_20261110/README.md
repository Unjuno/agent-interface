# Xvfb cancellation release/autorepeat frontier (preregistered)

## Status and source freeze

Frozen before the first input trial. Test-only delay parameterization is at
source commit `806169d7653b8b0228a548d5013ed2ee9a47637f`; this descends from
current main `0ac46b03f291ec5805d4ab54b70d8e7b7bad5e99`. It changes the existing
Xvfb integration fixture's delayed XTEST request from a fixed 8000 ms to a
bounded environment-controlled value (1–8000 ms); the production runtime is
unchanged. Exact source tree, cached image digest, and runtime conditions are
recorded in raw metadata before execution.

## Question and hypothesis

The prior matched trial observed standard-arm release readback at 848 ms and
five autorepeat KeyPresses after the initial event; the prestarted arm's two
readbacks were about 365 ms and its independent effect count was one. Does the
effect-multiplicity boundary move with XTEST request delay and cancellation
path, under this same private-Xvfb application and server configuration?

Hypothesis: standard cleanup will cross the server's initial autorepeat delay
at shorter injected request delays than cleanup through the prestarted
supervisor. The threshold and effect of each route remain unknown; this is an
exploratory latency-to-correctness frontier, not a reliability estimate.

## Frozen design

- A = standard guarded caller (`AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=0`).
- B = guarded caller with prestarted cancellation supervisor (`=1`).
- Delayed XTEST request `time` values: 100, 250, and 500 ms.
- Two replicates per arm/delay, 12 attempts total, fixed order:
  `A100, B100, B250, A250, A500, B500, B500, A500, A250, B250, B100, A100`.
- Each attempt uses a fresh private Xvfb and Python test process, the same
  pinned cached image, same source, ACK-withhold interval (1 s), cancel bound
  (3 s), transaction bound (4 s), terminal bound (5 s), synthetic target and
  independent task-effect oracle. The only planned factors are A/B and delayed
  XTEST request time. Xvfb keyboard repeat settings are not changed; the image's
  default is part of this condition.
- Primary endpoint: exact synthetic application effect count for the initial
  `a` task input (expected one), independently counted through the parent X
  client at the release horizon. Record every repeated event and timestamp.
- Secondary endpoints: cancellation response latency; release-attempt and
  independent keymap readback latency; final/horizon key state; old delayed
  `b` event; fresh-target task oracle; runtime custody status. Runtime UNKNOWN
  is never upgraded by fixture readback.
- Every attempt runs once. Continue after a task-oracle or assertion failure
  only when the attempt report exists, final cleanup is not reported failed,
  and its owned Xvfb exits. Stop immediately on missing report, failed final
  cleanup, or live Xvfb. Preserve all attempted outcomes; no retry or
  replacement trial.

## Decision and interpretation

The sweep is informative only if all scheduled attempts and process records
reconcile. Report the observed effect-count boundary by arm and delay without
fitting a reliability curve or claiming statistical significance. The result
may show a route difference, no route difference, or an inconclusive boundary.
Any exact-count failure is a task failure even if key state is eventually
neutral. Any missing release/custody receipt remains unknown. No result here
establishes physical GUI behavior, WSLc, MAP01, provider efficiency, broad
reliability, or general project completion.

## Execution

`run-frontier.sh` runs the frozen 12-cell schedule in the existing cached image
with network disabled, read-only source, private tmpfs, and a dedicated writable
output mount. Raw logs and per-attempt JSON are retained separately from this
pre-registration; a SHA-256 manifest is added after execution.
