# Native Win32 process-retirement and SendInput recovery — R01

**Disposition: `ABORTED_BEFORE_ACTION`.** The frozen runner failed while
importing `runtime` because direct script execution did not put the repository
root on `sys.path`. It stopped before `main()`, Win32 API access, fixture
creation, process startup, or input. `raw.json` was absent, and no probe child
process existed. The exact error and frozen source/condition hashes are in
[`construction_failure.json`](construction_failure.json). The original probe
and conditions remain unchanged. A corrected, separately frozen construction
is retained as [R02](../win32_native_supervised_sendinput_hook_20261024_r02/README.md).

## Question and scope

When a disposable Win32 producer is blocked inside a real `SendInput` call by a
short `WH_KEYBOARD_LL` callback, can the current process-cancellation
supervisor retire that exact producer, issue one compensating UP from its
prestarted recovery process, and obtain an independent Win32 all-up readback
before a finite deadline? The test binds the operation to the actual target
generation of a small owned EDIT fixture. It is one native input event, one
producer, one recovery attempt, and one independent readback.

This is a narrow native recovery discriminator, not standard MCP caller
qualification, task-effect evidence, a reliability estimate, or a guarantee for
an indefinitely blocked call. The F13 event has no task oracle; `task_success`
must remain null. No WSLc or Docker allocation is used.

## Frozen conditions

- Run once on this interactive Windows PC, using a visible owned EDIT window as
  the only configured target. Restore the prior foreground window and destroy
  the fixture at cleanup.
- The child installs `WH_KEYBOARD_LL`, opens a parent-owned start gate, and
  calls the real Win32 backend's `SendInput` once for injected F13 down. Its
  matching callback waits at most 200 ms. The parent requests cancellation as
  soon as it observes callback entry.
- Recovery and independent observer processes are started and report ready
  before producer admission. The supervisor must confirm the exact producer
  process exit before recovery is allowed. Recovery rechecks the frozen HWND
  generation, sends F13 UP once, and reports its runtime release receipt. The
  separate observer rechecks generation and reads F13 state through the
  backend's independent state witness.
- Cleanup deadline: 2500 ms from the cancellation request. Late-state horizon:
  1500 ms after independent recovery readback. An absent receipt, stale target,
  or ambiguous input state is UNKNOWN; no replay or second recovery attempt.
- If the supervisor does not confirm neutral state, the runner may make one
  separately labeled emergency UP only after its cancellation thread has exited
  and the exact producer process is confirmed retired. That cleanup cannot
  convert the experimental outcome to PASS.
- The hook briefly covers the interactive desktop, but only injected F13-down
  callbacks are delayed. No registry, privilege, process, or application state
  outside the owned fixture and test child processes is changed.

## Decision rule

PASS for this one schedule requires hook entry while the producer is still
inside its native call; a bounded cancel response; confirmed exact producer
exit before the recovery helper's SendInput UP; valid generation-bound recovery
and independent all-up readback before 2500 ms; and an independent all-up
sample after the 1500 ms late-state horizon. Any uncertain condition remains
UNKNOWN. This does not qualify the standard public caller or application task
success.

## Evidence

- `conditions.json`: fixed conditions and source bindings.
- `probe.py`: one-shot live probe; refuses to overwrite `raw.json`.
- `raw.json`: exact process, hook, API, supervisor, recovery, readback, horizon,
  and cleanup records.
- `audit.py` / `audit.json`: independent hash, ordering, deadline, state, and
  cleanup audit.

No scientific run occurred in R01.
