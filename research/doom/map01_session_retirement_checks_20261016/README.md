# MAP01 session: stop engine effects at unresolved input retirement

2026-10-16. Base `d30baae1bf668d462a763bdc2e8cd11cc7a7515e`;
tested code `7dc8c132c16661767b9806ac7a4a86d330be107a`.
Local/Fake X only. No live game, GUI, provider, WSL or container allocation.

## Caller defect and repair

The selected session main normally owns one backend. Its `finish` and
`save_fixture` branches nevertheless treated `Executor.close()` as sufficient
retirement. Close can return with a retained failed/unverified release or an
unstarted active intent after ambiguous accepted-event publication.

The original command loop, with a real selected ExecutorV13/process backend and
Fake X release-send held, advanced the stub game and published a post-control
score after failed release. Its fixture branch saved, advanced and published a
fixture. A separate ambiguous unstarted intent also passed into finish. Those
first RED outputs remain retained. These are observed calls to a stub engine,
not measured real game effects or a false-success claim about a prior live run.

Both branches now call `close_before_control_effect`: close the Executor, inspect
closed/active/original obligation under its lock, and proceed only when it is
closed, inactive and obligation-free. Unresolved state is saved exclusively to
`control-boundary-failure.json` before external emission, then the command raises.
The record keeps the original obligation, operation and active intent, with task
effect unknown and no grant of input authority. Saving or delivery errors also
stop before engine effects; an existing failure file is never overwritten.

| Check | Evidence / result |
|---|---|
| Original failed release, key38 still held | Both actual command branches refuse; no advance, save, score or fixture event before the gate resumes |
| Ambiguous accepted publication, unstarted intent | Finish refuses even with an empty fake key bitmap and no release obligation |
| Failure receipt collision / external mutation and delivery error | Original file remains; newly saved active-intent evidence precedes and survives sink mutation; no engine effects |
| Executor close error | Original error propagates before engine effects |
| Healthy verified retirement | Existing finish refresh/score and fixture Save/refresh paths remain available |

The new tests extract the actual command loop and top-level pure helper
definitions using AST, without importing/starting VizDoom or running its setup.
Only engine effects are stubbed. The separate existing nine cleanup tests execute
the actual outer finally block. This is not a full engine/session-process run or
combined fault injection through setup, command processing and outer cleanup.

## Validation and source custody

Normal and optimized affected runs each cover **54 modules, 395 methods, 11
explicit skips (384 executed), zero failures**. The existing regression entry now
includes the five new retirement methods and nine existing session cleanup
methods. Each module's output and summary are retained here. The optional real
Codex handshake and platform-specific tests remain skipped as reported.

The first three-method RED run had three subtest/method failures. Initial GREEN
had two fixture assertion failures because JSON converts an identity tuple to a
list; the test now compares canonical JSON values, preserving all identity
fields. The final five-method test source against the exact base session source
produces five failures (the two receipt-fault subcases also demonstrate effects
were not fenced). That pinned RED control and the first outcomes are retained.
The repaired five methods pass normal/-O within the full affected runs and review.

`MANIFEST.json` binds base/tested sources, command exits and every packet member.
The pinned RED control uses the base session file with the tested-code test file;
unchanged selected backend/Executor dependencies come from the working checkout.
It is a source-seam control, not a checkout-wide replay of an old live experiment.

## Remaining work

This closes a real command-layer bypass of the existing single-session custody
state. It does not repair the
[distinct-backend admission counterexample](../map01_cross_backend_custody_20261016/README.md),
establish durable/shared authority, provide automatic recovery or prove task
success. Close, file I/O, external emission and native release can still block;
there is no new physical or end-to-end time bound. Independent effect scoring
must be qualified with the chosen live engine/caller once a permitted fresh run
is available. The active #59/#17/#2437 objectives remain unmet.
