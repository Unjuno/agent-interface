# Win32 prestarted producer boundary (2026-11-17)

## Finding

R270 (30 s authority lease) and R273 (90 s authority lease) both returned from the public caller's producer `Process.start()` 47 ms after expiry. R273 therefore emitted no program actions and did not test the application effect. R274 independently reconciled that source as `not_dispatched`, retained the source action as UNKNOWN, and cleared custody after verifying producer absence and LEFT/W/SHIFT up. See the merged [R273/R274 report](map01_r273_current_main_public_caller_start_20261117/REPORT.md).

Current-main source inspection at `60a410800902dd37513b305facf96f246d00eba0`:

- `runtime/cli_v1/mcp_server.py::_run_supervised_win32_dispatch` normalizes the supplied program, binds a generation, admits the operation, then calls `owner.start_producer` synchronously.
- `runtime/cli_v1/owned_win32_session.py::start_producer` calls the factory, then `process.start()`, then obtains/verifies process identity, rechecks generation, registers the process and opens its start gate.
- `runtime/cli_v1/win32_standard_producer.py::NativeWin32StandardProducerFactory` creates a new one-use `multiprocessing.Process` per call. The child waits on a closed Event gate, dispatches one program, writes one result packet, and exits.
- The recovery and completion-observer helpers are already persistent and ready before action admission (`OperationCancellationSupervisor` / `NativeWin32SupervisorHelperFactory`). They do not prestart the native producer.

So the existing gate correctly prevents late input, but does not remove producer creation/startup from the user's authority interval. Increasing the lease cannot be treated as a fix based on the two observations.

## Integration contract to preserve

The next candidate should keep one-use producer semantics while moving process readiness to a reusable, prewarmed worker slot outside any action lease. For each action, the parent must send a bounded immutable request to the already-started idle worker; receive a ready acknowledgement bound to call ID, operation ID, target generation, and request digest; revalidate the exact current target generation; register the exact process identity with custody; then authorize the worker's private input gate. The worker may not construct an input backend or emit input before that authorization. After one task it must retire; the pool replenishes the slot only after the old worker's terminal result/retirement is accounted for. Cancellation, timeout, stale generation, malformed acknowledgement, pipe loss, or worker death before authorization must fail closed and preserve UNKNOWN unless no-dispatch is independently proved. No worker may be reused while its former action or custody is unresolved.

A ready worker should be warmed at supervised-server startup and while no action lease is held. If no ready slot exists, the caller must report bounded unavailability before issuing authority, rather than start a worker under a lease. This changes the surrounding caller contract and needs an explicit typed pre-admission outcome; it is not a local substitution of `Process.start()` with a thread.

## Required composed-path regressions

1. Prepared worker is already alive before authority creation; startup time is charged to lifecycle/setup, not task lease.
2. Exact request/ack identity and digest mismatch refuses before gate open or native backend construction.
3. Target-generation change after warmup but before authorization refuses with gate closed and zero program actions.
4. Cancellation before request acknowledgement, after acknowledgement, and during dispatch retains exact worker identity, closes admission, retires the worker, and does not replay.
5. A second call cannot borrow the first call's worker or custody; replenishment is separately timed and bounded.
6. Worker reports completion but remains alive: public action is not completed until exit/neutral observation and existing terminal/release requirements pass.
7. Missing result, pipe loss, delayed acknowledgement, or restart while custody is unresolved cannot clear source UNKNOWN or admit a successor.
8. Public MCP tests exercise the same supervisor, custody fence, target generation reader, late-input horizon, and result readers used by the native route, in normal and optimized Python.

## Measurement boundary

Compare current one-process-per-action route with the prewarmed one-use worker route using identical MAP01 task, model path (none for this native mechanics probe), target checks, effect oracle, lease semantics, and all-attempt accounting. Report separately: server/worker cold startup, ready-slot wait, action interval, generation check/IPC/authorization, worker run, retirement/release, neutral horizons, and independent ammo score. Any pre-input timeout remains an attempt and is not retried under the same allocation. This mechanics probe alone is not an efficiency comparison or task-effect pass; the eventual #57 comparison still requires its frozen three-arm accounting and current v3 caller integration.
