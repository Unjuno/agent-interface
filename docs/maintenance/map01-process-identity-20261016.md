# MAP01 process identity integration: Fake X only

Explicit V39 `--measurement-session --target-process-identity` selection connects
image-bracketed process identity through Executor admission to the selected V12
owner. Defaults remain unchanged. Capture and owner use separate read-only
target-query workers, keeping these reads off the input connection. This requires
a trusted local X server with XRes and a matching Linux PID namespace.

The strict pointer binding keeps its three original fields. Separate observation
metadata carries sequence/XID/process digest. Admission binds this once to the
original lease deadline before `accepted`; repeat binding is refused. The owner
checks the bound source before input, after its final focus query, and every
20 ms while held. Missing/changed/unavailable identity refuses new input and
revokes held authority. Cancellation/expiry end the wait for a blocked identity
read; the retired reader cannot reconnect in that session. Selected release
receipts preserve pending-reader retirement state. V4/V3/V12 telemetry and the
single input writer remain in use. V15 adds a repository-root identity manifest
separate from the existing research-relative source map.

## Verification

The new owner, composed backend and caller-selection tests contain 15 methods.
They use actual capture/publication, Executor, V4 and V12 with Fake X clients and
fake signal readers. Cases cover fresh input/release, stale refusal, capture
mismatch, missing source, accepted-callback source replacement, blocked identity
cancellation/original expiry/stop, late reply retirement, and final focus-query
mutation of cancellation/source/deadline.

Read-only review of `d3dcffdbdc9a83959f1d0133d54159450afebda1` found that an
accepted callback could use the supported binder again to replace sequence 1/A
with sequence 2/B before the first press. The added regression failed before
repair; the binder now refuses repeat binding. First RED is preserved.

A module-isolated normal/-O sweep ran 33 modules / 243 methods in each mode.
31 modules / 227 methods completed without failure, including one deliberate
real-Codex handshake skip. Two older release-composition modules (16 methods)
still fail: fake owners lack `up_batch`, fake leases lack `check`, and old ledger
expectations differ from the buffered-UP path. The same failures reproduce on a
source-only snapshot of exact base `067bc1ad7ef2fb226256089c17766a4048428322`:
1 failure/1 error and 8 failures/22 subtest errors respectively. They are not
counted as passing. Initial import failures came from generic `session_v7` name
collisions; isolated processes with live_control-before-doom PYTHONPATH resolve
them. A first baseline attempt used the sparse primary checkout and lacked test
files; the subsequent source snapshot materializes all needed Python files.

First RED, sweep and baseline logs, drivers and source snapshot are retained
locally under the existing consolidation evidence directory:
`C:\Users\user\Documents\Codex\2026-10-03\new-chat-2\outputs\repository-consolidation-20261015`.
These are local receipts, not portable published raw. Historical generation-gap
source/raw remain unchanged; current implementation does not rewrite that result.

## Limits and next finite cleanup

Process incarnation does not establish window incarnation or atomic server
acceptance. Native focus, send/sync/readback and capture can still block. A
pending read-only daemon can outlive owner cleanup until its I/O returns. No
physical release bound, live GUI/provider, task effect, bounded task recovery or
matched efficiency result is claimed. #59 and the broader goal remain open.

Repair the two old release-composition fixtures against the current batch
protocol while preserving provenance, malformed-receipt and delivery-ledger
assertions. This is a concrete outstanding cleanup item for the next worker.

### Fixture cleanup follow-up

The stale fixtures now implement the supported `up_batch` protocol and retain
its ordered owner receipt fields. Tests of errors *after completed release*
explicitly flush before injecting the error. A separate new case verifies that
an UP buffered before an exception remains unknown/unverified. Manually injected
incomplete rows no longer coexist with a duplicate pending UP. Existing key,
cancellation, provenance, sink mutation and cumulative delivery assertions remain.
Production input/release code is unchanged by this follow-up.

The local sweep is reproducible with the same Python/dependencies used for the
tests (including python-xlib and Pillow):

```sh
python research/doom/check_map01_control_regressions.py --output-dir /absolute/fresh/normal
python research/doom/check_map01_control_regressions.py --optimized --output-dir /absolute/fresh/optimized
```

Each module runs in a separate process with explicit import paths. The runner
retains per-module logs, exact HEAD/dirty status and summary, refuses to reuse an
output directory, and deliberately skips the optional real-Codex handshake.
It does not launch a display, container, model or live allocation.

Final clean source `22633a3171cd72f6cef92ec1e5e1e2ab93de53c5`: normal and
optimized each report 33 modules / 244 methods, zero failures, one deliberate
handshake skip (243 executed). [Retained logs and conditions](../../research/doom/map01_process_identity_local_checks_20261016/README.md)
include all per-module outputs, original repeat-bind RED and exact-base fixture
RED. This resolves the local fixture task above without qualifying live gates.

The subsequent [selected focus isolation](../../research/doom/map01_focus_isolation_local_checks_20261016/README.md)
also routes lease-bound exact-focus reads through the independent worker. Actual
composed Fake X cancellation and original-expiry controls release while that
read remains blocked; late pre-press replies cannot inject input. Native input
I/O, pointer geometry/hit checks, physical and task-effect limits still apply.
