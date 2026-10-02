# Compiled method expiry into guarded X11 input

The compiled runtime already passes the minimum of admission and method
budgets to an executor, but NativeHandleBridge created a new five-second lease
for every action. The Python click/move/keyboard APIs now accept explicit
`expires_at_ns` in the execution host monotonic clock. The guard and core
program use the minimum of this deadline and the existing five-second cap.
Already expired callers refuse before capture/dispatch. Invalid deadlines
raise before activating a guard. Existing calls retain the default behavior.
Admission and capture cost cannot renew the deadline.

This is a necessary connection for the planned live compiled adapter, not that
whole adapter. MCP input schema and caller routing are unchanged. No sensor,
model, automatic replay, remint or task-success certificate is added.

## Verification

Six new regression tests initially failed at the unsupported API (12 errors
including subtests); the unchanged default test passed. With the implementation,
all 20 deadline/motion tests passed. Existing backend expiry tests cover stopped
waits/keys, permitted releases and retained release failures. The full local
native protocol and harness suites passed from committed source; exact logs
and runner metadata are under `native-ci`.

The explicit real Xvfb/Tk case uses a program-selected, fixture-authored target.
It is a program verification, not primary-model image grounding or a task-efficiency
trial. Source commit is pinned in REPORT.json and every real input receipt/image
is retained. The oracle reads Tk event records only after bridge and children
have terminated. The successful third case emitted exactly one button press,
failed at wait op 4 with a one-second caller deadline inside a requested two-second
wait, never emitted the following `must-not-run` text, and returned verified
empty key/button release. The immediately expired action emitted no input.

Both earlier fixture failures remain: case `live` picked a flat blank entry crop
and mint refused before input; `live-02` used Tk's inner window ID instead of its
focused wrapper, so focus guard refused with zero emissions. Separate `live-03`
corrected the fixture ID and reference crop, without weakening production guards.
Each allocation's child exit codes are retained. These retries diagnose setup;
no selected trial is used to claim a rate, latency distribution or improvement.

Cooperative expiry can be detected late after scheduling or blocking X11 calls;
it does not guarantee physical release by the deadline or undo earlier effects.
The full conditional live adapter, independent task correctness and comparable
primary-model timing/cost evaluation remain open. This report makes no speed,
token-saving, model-resumption or human-performance claim.
