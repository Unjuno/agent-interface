# Native Win32 process-retirement and SendInput recovery — R03

R01 stopped before module import because the repository root was missing from `sys.path`; R02 reached the owned fixture and target-generation binding but stopped before producer start because the recovery helper's ready receipt did not match the supervisor's exact protocol. Both outcomes and raw are preserved in their own packets. R03 changes only the helper's initial receipt to `{"status":"ready","helper":role}`. Runtime sources, native stimulus, deadlines, fixture, and analysis remain frozen as specified below.

**Run count: one.** `raw.json` must not exist before the run. The experiment is permitted on this interactive Windows PC, using only F13 and a small visible owned EDIT fixture. No WSLc allocation or Docker is used. No registry, privilege, or system configuration is changed. If preflight fails before producer start, preserve that as an abort and do not repeat this packet. If the native stimulus begins, run the fixed supervisor/recovery/readback flow once and retain every result, including UNKNOWN or FAIL.

## Question and scope

When a disposable Win32 producer is blocked inside a real `SendInput` call by a short `WH_KEYBOARD_LL` callback, can the current process-cancellation supervisor retire that exact producer, issue one compensating UP from its prestarted recovery process, and obtain an independent Win32 all-up readback before a finite deadline? The test binds the operation to the actual target generation of a small owned EDIT fixture. It is one native input event, one producer, one recovery attempt, and one independent readback.

This is a narrow native recovery discriminator, not standard MCP caller qualification, task-effect evidence, a reliability estimate, or a guarantee for an indefinitely blocked call. The F13 event has no task oracle; `task_success` must remain null.

## Frozen conditions

- One visible owned EDIT fixture; target generation from `Win32Backend.target_generation`.
- One spawned producer; one real `SendInput` VK_F13 down; a low-level hook blocks only injected F13 down for at most 200 ms.
- One prestarted recovery helper; only after exact producer retirement, recheck the same HWND generation, then one real `Win32Backend.release_all` UP.
- One separately prestarted observer; same generation check and backend state witness.
- Recovery deadline 2500 ms; late-state horizon 1500 ms; monotonic `perf_counter_ns` clock.
- PASS requires hook entry before producer return, cancellation response <=250 ms, confirmed producer exit before recovery UP, generation-matched release and independent readback before 2500 ms, all-up after the 1500 ms horizon, and confirmed fixture/process cleanup.
- Missing/stale generation, uncertain producer identity or retirement, helper failure, unknown state, timeout, or incomplete cleanup is UNKNOWN. No replay or second recovery attempt.
- Emergency UP is allowed only after cancellation thread stop and exact producer retirement; it is separately labeled and cannot produce PASS.

## Evidence

`conditions.json` binds the one-shot scope and source hashes. `probe.py` refuses to overwrite raw output. `raw.json` will retain exact IPC, process, hook, API, recovery, observer and cleanup events. `audit.py` and `audit.json` are a read-only hash, ordering, deadline, state and cleanup audit. R01 and R02 construction outcomes remain immutable in their respective packets.

## Result

**Disposition: `PASS` for this one finite schedule.** The independent audit passes
20/20 checks. The hook callback began before the producer returned from its
blocked `SendInput`; cancellation returned `pending` in 0.1971 ms; the exact
producer exited before recovery UP; and the same-generation recovery and
independent all-up readback completed 14.2328 ms after recovery began. The
independent observer still saw all-up after the 1.5 s horizon. The runner
reported no errors, no emergency UP was needed, and process/supervisor/fixture
cleanup succeeded. `task_success` remains null because F13 has no task oracle.

`raw.json` SHA-256:
`3048d66f6a4c69e266878764b8b870069fae36010665c6fd8b8d59adba01bbd5`.
The audit disposition and every check are in `audit.json`. This does not
establish an unbounded release guarantee, standard public caller integration,
MAP01 task success, other failure modes, or a reliability rate.
