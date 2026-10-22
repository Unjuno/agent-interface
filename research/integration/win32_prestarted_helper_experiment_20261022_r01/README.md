# Prestarted helper process experiment (Win32 inert model)

**Disposition:** `PASS_MODEL_SCOPED`; research prototype only. This packet
tests process-start ordering with multiprocessing `spawn`, shared-memory
fixtures and inert helper functions. It imports no Win32 API, does not emit
input, and is not a public-MCP or native-Windows result.

The first RED test copied the existing `InertOperationOwner` from the immutable
PR #9404 packet and counted child starts. It observed one process created
before cancellation and three afterward (`3 != 1`): recovery and observation
helpers were started inside the cancellation method. The candidate now starts
both helpers and receives explicit readiness before it can admit an operation.
Cancellation reuses those helpers and waits for a per-request completion
message; it performs no process creation. If either helper is missing or dead
before admission, the producer is not started. If helper work or retirement
misses the cancellation deadline, the result stays `UNKNOWN` and replay is
denied.

The frozen candidate source is [`operation_owner.py`](operation_owner.py), and
its composed process tests are [`test_operation_owner.py`](test_operation_owner.py).
The first observed REDs are summarized in
[`raw/r01/red-observations.json`](raw/r01/red-observations.json). The final
normal and optimized test logs, exit codes, and conditions are retained under
[`raw/r01/`](raw/r01/). File hashes are in [`artifact-sha256.txt`](artifact-sha256.txt).

The candidate starts recovery and observer processes synchronously during
owner initialization. This blocks initialization before any operation can be
admitted; it does **not** prove a bounded server-start time. The operation
producer is still started in `begin()`, so producer startup latency is also
outside this cancellation-specific result. `terminate`, `join`, scheduling,
pipe delivery, and OS input behavior are not hard-bounded by this model.

The positive fake result means only that the injected model saw producer
retirement, a fake compensating UP, a fake neutral readback, and completion of
the helper request. The original operation remains `unknown`, task success is
null, and replay is false. It does not establish physical release, late-event
exclusion, independent task success, a usable Win32 supervisor, public MCP
integration, matched efficiency, reliability, or WSLc portability. No WSLc,
Docker, native input, or desktop target was used.

## Result

At main `0c20307cc43579c382eb31dae2ac9f593ea0f1d1`, Windows CPython 3.11.9
passed 14/14 tests normally and 14/14 with `-O`. The cases include accepted-
then-blocked and before-acceptance producers, helper startup failure,
helper loss before admission, helper timeout with `UNKNOWN`, no process start
during cancel, no recovery before producer retirement, and no producer overlap
when retirement is uncertain. These are finite synthetic schedules, not a
reliability estimate.
