# Win32 R10 — post-expiry cancellation, delayed-input horizon, fresh task

R10 is one finite current-main standard MCP/Win32 fixture run, based on main
`745ffe22e02af08e65eca4d638beb998384ae7a8`. It reuses the immutable R09
two-phase fixture protocol but has a new target name, attempt ID, run directory,
and conditions. R09's raw files are read-only reference evidence and will not be
changed.

## Frozen phase 1: input held across authority expiry

Start one repository-owned disposable Win32 fixture, take a public observation,
then dispatch one program that presses SHIFT and attempts SHIFT-up. The producer
injects a hold inside the child process immediately before native `SendInput`
for SHIFT-up; independently read native state must show SHIFT down while held.
The dispatch authority expires eight seconds after the frozen deadline is
created. With public-caller cancellation policy and its maximum two-second
handoff grace, a public `interface_cancel` at deadline minus 500 ms must return
`cancel_not_due`. After the same authority deadline, one public cancellation
must recover within the existing three-second cleanup bound and report verified
release on the exact call, operation, and target generation. The blocked child
must exit. Observe native SHIFT state for a two-second late-input horizon at
20 or more samples, maximum 100 ms sample gap, all SHIFT-up on one generation,
and no fixture effect events.

If any phase-1 condition fails, retain the first outcome, close/clean up the
fixture, and do not attempt phase 2 or retry R10.

## Frozen phase 2: generation fence and independent task receipt

Only after phase 1 passes, close and retire that fixture/session. Start one new
fixture process and session with a distinct PID and target generation. A
focus-only dispatch bound to the old generation must be refused with
`TARGET_GENERATION_CHANGED` and zero input. Then `run_public_compiled` may send
exactly one click/type/save task to the fresh fixture. Its exact expected effect
is `{saved: true, text: "office", clicked: true}`. Require the public result,
verified neutral input state, post-dispatch observation ordering, and an
independent server task oracle receipt bound to the exact action call ID,
operation ID, and fresh generation. The fixtures must exit cleanly and the
original foreground window must be restored.

## Acceptance and limits

Accept only if every machine-checked condition in `audit.py` passes and all
pretrial/raw hashes reconcile. One failed or unknown check is a retained failure;
no retry or result substitution. This is an isolated Windows fixture experiment,
not a MAP01, real application, model/provider, efficiency comparison, WSLc or
Docker trial. It tests the bounded injected pre-`SendInput` hold and delayed
input after authority expiry; it does not establish OS/kernel `SendInput` hang
recovery or an arbitrary-I/O guarantee. One pass does not establish repeated
reliability.
