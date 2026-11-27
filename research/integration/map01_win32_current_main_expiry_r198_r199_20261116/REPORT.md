# MAP01 Win32 current-main expiry recovery R198/R199 (2026-11-16)

This packet preserves two separate one-shot native Windows MAP01 attempts against current main `86a52662dc2bb690dd670d52ea8d97816aef2a26` / tree `c35b16d1df4f2e7c6b70a09e2ec672043ace5335`. No runtime source changed. Both use the pinned R193 candidate runner and unique trial directories; R199 is a fresh attempt, not a replay of R198.

## R198: effect observed, frozen projection mismatch

R198 observed the calibrated ammo HUD transition 50→49, excluded the delayed second click, confirmed separate releases and both horizons, and returned normally with custody clear. However, its frozen `query_projection` expected source action `unknown` / release false while current main returned `recovered` / release true. Preserve the runner PASS label as raw output, but independent adjudication withholds full preregistration pass. The source/test crosswalk shows confirmed recovery maps to `recovered` and release true while task success remains null. This is an experiment-condition mismatch, not a demonstrated runtime bug. See [R198 audit](r198/LOCAL_AUDIT_REPORT.md).

## R199: corrected frozen projection passes

R199 froze the current-main projection (`recovered` / release true when the joined recovery proof matches; `task_success=null`) before launch. It passed the scoped expiry, delayed-operation exclusion, release, effect, custody and cleanup gates: one dispatch/recovery, one observed ammo change 50→49, delayed click excluded, 32 ms expiry-to-release, 75 integrated late-input observations across 2 s (max gap 32 ms), independent neutral horizon VERIFIED across 2 s, normal target exit, and clear custody. The independent adjudicator confirms all frozen projection fields match. Task success remains null; this is a single observed task effect, not semantic task success.

See [R199 audit](r199/LOCAL_AUDIT_REPORT.md), [preregistration](r199/PREREGISTRATION.md), and [machine adjudication](r199/ADJUDICATION.json).

## Scope boundary toward Issue #57

These runs establish one scoped live effect/recovery slice. They have no model/provider calls, token totals, billing evidence, or matched direct/compiled/fresh arms. Do not pool R198 and R199 as independent reliability or speed evidence; R198 is condition-deviant and R199 is one valid trial. The existing four-pair Docker/Xvfb caller comparison is a separate local timing study (compiled median 921.986 ms vs direct 878.026 ms; paired median +43.435 ms, n=4) with no provider/token accounting. The closest current-main native Win32 recovery route block R237–R240 also found compiled slower: +11.7% at descriptive n=2 arm medians, with no provider calls and outer lifecycle timing excluded. Neither study establishes integrated token efficiency; Docker was not used for R198/R199. The current #57 issue still requires same-task/model lifecycle accounting across cold/warm/invalidation/repair, all attempts, correctness, latency, model usage and recoveries.

### Next comparison discriminator

Use a prospectively frozen same-model GUI task with matched direct, compiled-continuation and fresh-regrounding routes, counterbalanced order, and one attempt per arm/block. Count all setup/startup and preparation consistently, capture each model/provider call's input/output/cached tokens and latency with an independent usage receipt, preserve failures in denominators, and record release, task effect/success, invalidation, repair and total wall time. Keep model/provider usage out of scope unless an existing no-extra-charge authorization and attributable usage source are verified. WSLc remains STOP/HOLD under [#7924](https://github.com/Unjuno/agent-interface/issues/7924); this packet used only the previously authorized Windows PC.

## Closest current-main route comparison (R237–R240)

The earlier same-host native Win32 ABBA block in the preserved local packet `private-packets/map01_native_windows_current_main_r217_exception_recovery_20261114/runner-candidates/r225-spawn-phase-profile/` is the closest route comparison, not R199. Its four frozen trials all passed the scoped 50→49 effect, release, late-input horizon and neutral horizon gates with `task_success=null`. Direct median was 3.0800423 s (n=2); compiled median was 3.4401911 s (n=2), a descriptive +0.3601488 s / +11.7% for compiled. Compiled also used 120/125 result polls vs 96/97 direct. It had zero model/provider calls, began timing after the shared stable baseline, excluded startup/manual visibility gates, and did not instrument precise outer lifecycle time. Do not infer token savings or a general performance result. The full report is in current `docs/CURRENT_GOAL.md` and the exact local source packet remains at the path above; this new packet does not duplicate its raw bytes.

## Local verification

Against the same current-main source, `runtime.cli_v1.test_supervised_win32_compiled` passed 9/9 normally and 9/9 with `-O`. These focused logs exercise the recovered-vs-unknown source projection branch; they are regression evidence, not a model or GUI comparison.

- [Raw manifests](r198/RAW-MANIFEST.json) and [R199 raw manifest](r199/RAW-MANIFEST.json) give per-file SHA-256 and byte counts.
- The packet-level `MANIFEST.json` covers all packet files other than itself.
- Each `conditions.json` pins the exact runtime and runner/packet source hashes. R198 and R199 remain separate immutable records.
