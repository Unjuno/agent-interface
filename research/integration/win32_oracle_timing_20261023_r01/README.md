# Win32 independent task-oracle observation window — R01

Baseline `46640f28c58302e224af5673658773745afca356` checks oracle receipt
identity and requires a positive observation timestamp, but accepts success
with timestamp `1` or `2**63`. Thus it can accept an observation predating the
oracle request or one from the future, despite matching call/operation/generation
IDs. The public-path regression reproduces both false acceptances.

Code commit `79aa55c0d062213d4c3927e38485a45a2a335a56` records oracle reservation
time and requires `requested <= observed <= receipt_processed`. A stale/future
observation raises a receipt validation error; the public route retains
UNKNOWN, task success unset and replay denied, with no second oracle call on
duplicate verification. Unknown results preserve the original reservation time.
Accepted records preserve both timing endpoints; duplicate accepted receipts
return the same immutable result without changing the endpoints.

The public field `receipt_received_monotonic_ns` denotes receipt processing by
the parent owner, not initial network/IPC arrival, application completion,
redraw, or physical input effect. The oracle must use the same host monotonic
clock domain. Equality at either endpoint is allowed because clock resolution
may produce equal readings. Tests use hand-checked endpoints 100 and 200;
these are synthetic values, not measured application latencies.

## Evidence

- `raw-red.txt`: initial two false-success failures plus two missing-new-field
  errors in the newly introduced endpoint tests, before implementing the fix.
- `reproduce_baseline.py`: substitutes the frozen pre-fix owner class in
  memory and runs the final public regression. `raw-baseline.txt` contains the
  two expected failures; repository source files are not modified by the probe.
- `raw-first-green.txt`: 27 passes before adding the explicit error-reason
  assertion to the negative test.
- `raw-normal.txt` / `raw-optimized.txt`: 27/27 final tests pass per mode,
  including public caller, local owner, actual backend/inert-API composition,
  timeout/late-receipt immutability, fresh-generation separation, and both
  timing endpoints. Commands, counts and exit codes are in `conditions.json`.
- `SOURCES.json` binds selected canonical Git blobs; `SHA256SUMS` covers
  packet files except itself. Earlier packets remain unchanged.

## Remaining authority and effect gates

This is a necessary timestamp-consistency check. It does not authenticate an
oracle that lies about time, independently prove the reported task effect,
measure effect latency, or establish causality between input and task success.
Current recovery requests retain frozen operation/generation IDs, while actual
current-target and input-domain authority remain helper responsibilities. A
changed target window and revoked global-input authority are different cases;
one additional parent query cannot atomically fence native recovery.

Native input/release, live MAP01/task effect, recovery authority, queued-input
semantics, matched efficiency and repeated reliability remain unqualified.
This work used no native desktop input, WSLc allocation, or Docker.
