# Win32 native supervisor recovery R05

## Scope and frozen question

On 2026-10-26, run one trial on this user-authorized Windows workstation against a freshly spawned `runtime.backends.win32_v1.fixture_app` process. The frozen condition is in `conditions.json`; the current source is `f2f7dbb2e043919e0773655e5fab543cc3682fcd`. No WSLc or Docker resource is touched.

The standard public MCP session will observe the fixture and dispatch one four-operation program: focus, SHIFT-down, SHIFT-up, release-all. The producer-local `user32.SendInput` callable blocks only at the SHIFT-up entry and signals the parent. The parent confirms that real SHIFT-down is active, sends one public `interface_cancel`, then records retained terminal custody and performs an independent same-generation key-state readback. The native recovery helper is production code. No task action is attempted; the fixture effect file must remain absent.

## Frozen classification

Pass only if the public observation and preflight generations match; the real key is down during the block; one cancellation request is issued; producer retirement and supervisor recovery are reported as recovered with verified release; the owner recovery latency is below 3,000 ms; a separate native readback sees SHIFT-up on the same generation without emergency input; the fixture effect file stays absent; and fixture process cleanup and foreground restoration are recorded. Any other first outcome is retained as `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED`. No retry is allowed under R05.

## Limits

The block occurs in an injected Python callable before native `SendInput` runs. It tests the standard caller and actual separate-process release/readback after a platform-call-boundary fault; it does not prove Windows or the kernel can hang inside `SendInput`. One sample cannot establish a hard deadline guarantee, reliability, task completion, MAP01, WSLc transfer, AppServer/model integration, matched efficiency, or production-app behavior.

## Retention

`run/` is created exclusively. The complete outcome, public call artifacts, target/process identity, input-state witnesses, fixture logs, timing and cleanup records are hashed after cleanup. Any failure remains immutable. Raw contains local process and file paths and stays local unless a sanitized export is separately created and audited.
