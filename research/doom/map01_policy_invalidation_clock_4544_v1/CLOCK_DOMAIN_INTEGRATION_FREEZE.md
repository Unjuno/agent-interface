# Host-monitor to Docker-runtime clock boundary experiment freeze

Date: 2026-09-27 (local)

## Question and H/T/D/C/U

- **H:** The actual `ObservableSignalPolicyMonitor` emits the hard-invalidation
  timestamp in the controller process's `time.perf_counter_ns()` domain. Three
  same-session host-send/runtime/host-receive probes can conservatively
  translate that timestamp into the pinned Docker runtime's monotonic domain;
  the actual final-admission gate then rejects the interrupted planner answer
  before Executor admission. A controller decision earlier than the translated
  invalidation must fail closed.
- **T:** One deterministic host-side harness imports the exact main-HEAD
  monitor and final-admission modules, produces one real monitor receipt from
  a fixed health reader (91 -> 68), samples a persistent pinned `linux/arm64`
  Docker process three times on the same session, and passes the receipt and
  calibration through the exact #4544 translator and final-admission function.
  Also pass the untranslated host receipt to the runtime-domain gate as a
  mixed-domain control. No model, game, GUI, or motor input is used.
- **D:** `PASS_SCOPED` requires a monitor `HARD_INVALIDATED` receipt with no
  claimed timestamp-domain field, complete ordered three-probe calibration,
  successful host->runtime translation retaining the source receipt, final
  `REJECTED_POLICY_INVALIDATED` with no input/Executor admission, and refusal
  when the controller decision precedes the translated invalidation. Any
  missing receipt/probe, exception, or failed condition is retained as
  `FAIL_OR_HOLD`; no retry or replacement run.
- **C:** This is one host/runtime clock-boundary instance with a synthetic
  health observation supplied to the real monitor. It does not establish the
  cause of #4516/#4532 or the seed-990641 running-action guard exception.
- **U:** No population clock-offset distribution, long-lived calibration
  validity, formal MAP01 horizon, GUI/game effect, latency benefit, or
  production authority claim.

## Frozen inputs

- Main base: `13cd6645b1bdd266bbe010f82ebcec2a573c23ed`.
- `observable_signal_guard_v2.py` Git blob: `c0955f976e3a0af6ce926f22cee4a5ddf70ef543`.
- `final_action_admission_v1.py` Git blob:
  `2b3875c5c885fac0a78db2e70cbaba30ca834c67`.
- #4544 translator SHA-256:
  `99ca937e911b89c1613f5be504ea64b416d98fe685a27f796900e44df887dfb0`.
- Frozen effective controller SHA-256:
  `53deb212a722f9d38d55e85d30eb9375ed3761c82c1f66554dbc4842931f7eeb`.
- Harness SHA-256:
  `5430ca99d15d3de63650ecf3c12bf447d58315a8d6146c93e6555550a325e37a`.
- Runtime image:
  `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`
  (`linux/arm64`).
- Fresh output path was absent before execution:
  `results/clock-domain-integration-20260927-01/`.

The exact source bytes and thresholds are not to be changed after this freeze.
