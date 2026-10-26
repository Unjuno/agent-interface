# Win32 native supervisor recovery R06

## Scope and frozen question

R06 is one new trial on 2026-10-26 on the user-authorized Windows workstation, using a fresh `runtime.backends.win32_v1.fixture_app` process. It corrects only the R05 harness parser, which compared a generation field on the outer review receipt rather than its retained raw report. R05 remains a no-input setup failure. The frozen conditions are in `conditions.json`; runtime source commit is `f2f7dbb2e043919e0773655e5fab543cc3682fcd`. No WSLc or Docker resource is touched.

The standard public MCP session observes the fixture and dispatches one four-operation program: focus, SHIFT-down, SHIFT-up, release-all. A producer-local wrapper blocks only at the SHIFT-up `user32.SendInput` entry and signals the parent. The parent independently confirms the real SHIFT-down, issues one public `interface_cancel`, then reads retained terminal custody and performs an independent same-generation key-state readback. The native recovery helper is production code. No task action is attempted; only the fixture `ready` event is permitted and its effect file must remain absent.

## Frozen classification

Pass only if the public raw observation and native preflight generations match; the real key is down during the block; one cancellation request is issued; producer retirement and supervisor recovery report verified release; owner cleanup latency is below 3,000 ms; separate native readback sees SHIFT-up on the same generation without emergency input; no task effect/event appears; and fixture cleanup and foreground restoration are recorded. Any other first outcome is retained as `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED`. R06 is not retried.

## Limits

The fault occurs in an injected Python callable before native `SendInput` runs. It tests the standard caller and independent real release/readback after a platform-call-boundary fault; it does not prove Windows or the kernel can hang inside `SendInput`. One sample cannot establish a hard deadline guarantee, reliability, task completion, MAP01, WSLc transfer, AppServer/model integration, matched efficiency, or production-app behavior.

## Retention

The exclusive `run/` directory is created once. Complete public call artifacts, target/process identity, input-state witnesses, fixture logs, timing, and cleanup records are hashed after cleanup. Any failure remains immutable. Raw contains local process and file paths and stays local unless a sanitized export is separately created and audited.
