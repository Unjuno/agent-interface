# X11 interrupt cleanup and session quarantine

Base main `3cf4b161100766e2e6b98ff485350f129d36f7e2`.
This is an ordinary Fake X repair and regression record. No live/native X,
game, model, WSL/container or historical formal allocation was run.

## Problem and change

An input operation raising `KeyboardInterrupt` or `SystemExit` escaped the
backend's `except Exception` cleanup. The X11 session also omitted those stops
from its quarantine handlers. The caller could catch the stop and continue
with neither a cleanup attempt nor a recovery requirement.

`X11Backend.execute` now attempts release on the same owner for propagated
`BaseException`, captures prefix/failed-op/release evidence as its latest
in-memory `interrupted_execution`, and preserves stop semantics. An original
non-Exception stop wins over a cleanup error or second stop. If ordinary input
failure is followed by a cleanup stop, the cleanup stop propagates with the
input failure as its cause. Ordinary execution errors retain their existing
`X11ExecutionError` result path.

The session sets sticky recovery-required state before propagating stops from
execution, preflight or failed preflight cleanup. An interrupted explicit
recovery leaves it required. Even a verified cleanup on an interrupted program
requires a separate explicit release-only recovery before new dispatch. This
does not replay the interrupted program. The guarded Python recovery still
revokes old aliases/history and requires review/fresh grounding.

The snapshot is owner-local memory, not a durable journal or a new transport
result. The caller must preserve it if retaining the interrupted execution is
needed. It remains available after explicit recovery; this fixture records it
in raw JSON stdout. Session replacement/new backend/process custody is outside
this repair. The API facade's caller-owned-session path is tested; shutdown
of an independently owned facade session is not newly qualified here.

## Executed checks and evidence

- Six backend/session test methods run actual public `dispatch_in_session`,
  admission, execute, `key_state`, release and readback methods. Only X transport,
  mapping/preflight and the injected text fault are memory doubles. Primary
  KeyboardInterrupt/SystemExit, healthy/failed/interrupted cleanup, both
  preflight-cleanup sites, preflight stop, explicit recovery and healthy input
  are covered. Prefix fake input is actually emitted before the injected stop.
- One additional method uses supported `NativeHandleBridge` observe/mint/input
  through public dispatch/session/backend, in two readback conditions. Only CTRL
  reaches fake transport; the suffix never presses. Failed readback retains its
  ledger even when fake state is neutral. Explicit recovery invalidates aliases
  and leaves task success unknown.
- The final seven methods pass normal and optimized Python. A separate ordinary
  control loads complete backend/session modules from pinned base main and runs
  the six new backend methods: ten assertion failures, zero errors. It is not
  replay of an archived producer or native experiment.
- [RESULT.json](RESULT.json) lists final affected suite counts and skips.
  [SOURCE_PINS.json](SOURCE_PINS.json) distinguishes tested Git bytes from actual
  checkout bytes and their AST equivalence. Raw initial fixture errors, original
  reproduction, composed repair, intermediate/final runs are preserved alongside
  [CONDITIONS.json](CONDITIONS.json). The first fixture reversed API arguments,
  then lacked its fake mapping boundary; both failed constructions remain.
  The first bridge fixture used an already-existing output directory and was
  corrected to a fresh child. These are construction repairs, not scientific
  retries or hidden excluded live failures.

## Remaining gate

This closes a scoped exception-unwind/custody hole. It does not interrupt a
blocked native send/sync/readback, bound physical release time, handle SIGKILL
or interpreter death, or qualify arbitrary repeated asynchronous interruption.
Fake transport state and release receipts are not independent application
effect. Cross-backend custody, device/read-access semantics, live task effect,
bounded semantic recovery and matched economics remain open in #17/#59/#57.
