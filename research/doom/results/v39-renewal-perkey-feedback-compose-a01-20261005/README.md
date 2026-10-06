# V39 renewal and per-key feedback composition A01

## Question

Can the current-main V39 stale-renewal recovery path and the optional A01 per-key measurement path coexist with the V15 scorer-only session without the wrapper silently replacing the selected backend?

## Change tested

The V39 controller can select V15 scorer sampling and pass the A01 per-key opt-in in the same session command. The V15 wrapper previously assigned its release-batch backend after V12 had selected the explicit A01 backend. The candidate preserves V12’s opt-in backend selection when that flag is present; the default V15 path continues to use its release-batch backend. A small selector helper is included in the V15 source manifest.

The composed controller also contains the current-main stale-sequence renewal recovery and typed per-key feedback projection from the two frozen input heads listed in `FREEZE.json`. This is an integration construction and source-level regression result only.

## Verification

- Base main: `1eac6ea9f5b91cc10a8c3dc20374b9d79ffcf179`; V39 controller blob: `cdf61eec2c030d7456b34a58907e9c43d5d72084`.
- CPython 3.12.10: `py_compile` passed for controller, V12/V15 session, and selector helper.
- Eight focused suites, including renewal recovery, wait/admission, controller cleanup, source refresh, typed feedback, legacy owner identity, and session/backend selection: 94 tests passed normally and 94 passed under `-O`; one POSIX-only pipe test is skipped on Windows in each run.
- The added selection regression verifies the V39 controller passes both V15 and per-key flags, and that V15 does not overwrite the A01 backend selected by V12.
- No live game, model, GUI, executor, or OS input was run.

## Limits

The integration remains unverified under an actual V15 session/game run. The retained trace gaps in Issue #59 remain: physical per-key up/release truth, application consumption, independently timestamped useful task feedback, prospective threat response, bounded live recovery, and MAP01 outcome. No live allocation is assigned or inferred. This package does not close Issue #59.
