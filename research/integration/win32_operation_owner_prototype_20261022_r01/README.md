# Win32 operation-owner inert prototype R01

Status: synthetic state-machine/process evidence only. This prototype never
imports the Win32 backend, calls `user32`, or emits native or desktop input.
It implements Phase 1 from the [operation-owner plan](../../../../docs/architecture/WIN32_OPERATION_OWNER_IMPLEMENTATION_PLAN.md).

The owner admits one operation with a frozen operation/session/generation and
input-obligation set. Cancellation first retires that exact operation process.
Only a confirmed exit permits a separate fake recovery process and a separate
fake readback process. A retirement failure returns UNKNOWN, emits no UP,
blocks later admission, and denies replay. After successful fake recovery, a
new operation requires a fresh session or target generation.

## Validation

Run the focused suite with:

```powershell
python -m unittest research.integration.win32_operation_owner_prototype_20261022_r01.test_operation_owner
python -O -m unittest research.integration.win32_operation_owner_prototype_20261022_r01.test_operation_owner
```

The test workers use `multiprocessing` spawn and shared in-memory fake state.
The before-acceptance and accepted-before-return schedules demonstrate only
that the prototype enforces its own process ordering. A passing result cannot
establish Windows `SendInput` ordering, OS-queue drainage, physical release,
independent platform-state observation, or target task success. Native
qualification remains gated by the implementation plan and Issue #7924 STOP
is unchanged.

## Retained runs

The packet files are listed in the [SHA-256 manifest](artifact-sha256.txt).

| Run | Result | Conditions and raw output |
| --- | --- | --- |
| r01 | `FAIL` — 12 tests executed in each mode; 11 passed and one failed. Recovery-start-failure test expected zero events, but the fake operation had already recorded one DOWN before cancellation. | [`raw/r01/`](raw/r01/) |
| r02 | `PASS_SYNTHETIC_PROCESS_ORDERING` — 12/12 tests in normal and optimized modes on Windows local CPython 3.11.9. | [`raw/r02/`](raw/r02/) |

r01 remains unchanged. r02 corrected the assertion to retain the already
recorded DOWN and verify that failed recovery startup adds no UP. Earlier
unrecorded draft attempts also exposed a test-only deadlock when the parent set
a multiprocessing event after forcibly terminating the waiter; the gate-set
was removed because a confirmed-retired process cannot be resumed. None of
these fake outcomes is a Win32 release result. The only current positive claim
is that the model permits fake recovery after its exact producer is observed
retired, then requires separate fake neutral-state readback. The operation
result stays `unknown`, task success stays null, and replay stays denied.
