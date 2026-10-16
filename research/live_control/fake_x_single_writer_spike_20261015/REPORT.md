# Single-writer observation separation — retained Fake X spike

Result: **PASS_FAKE_SEPARATION_NOT_PHYSICAL_BOUND**. Both frozen collections
(ordinary and optimized Python) met the ten predeclared trace gates and each
saved-only audit refused eleven mutations. This supports a separation seam;
the prototype is research-only and is **not adopted into the public runtime**.

Baseline/source context: main `30609dc1aa2a2a615e8ccb1ec77b317f0bd17a22`.
The user approved Fake X only. No real display, input, game/application, model,
WSL/container or live allocation was used. No task effect was scored.

| Boundary, in each interpreter mode | Coupled input/query owner | Separate query worker; one input owner |
|---|---|---|
| Healthy | CTRL/left then a/right; verified fake-neutral cleanup | Identical complete injection semantics |
| Cancel while query blocked | CTRL and left held; no cleanup receipt | Revoked epoch; verified fake-neutral cleanup before query resumed |
| Original expiry while query blocked | Same held prefix and absent receipt | Same separated cleanup; no deadline renewal |
| Duplicate cancel | Not a separate arm | Two requests, one revocation and one cleanup |
| Cleanup sync blocked | Not a separate arm | Fake state already neutral, no verified receipt until backend resumed |
| Cleanup emission blocked | Not a separate arm | CTRL and left still held until backend resumed |
| Cleanup readback fails | Not a separate arm | Fake neutral, result unknown; tracked CTRL/left obligations retained |

All ten cells per mode use one injection thread. All eight revoked cells per
mode discard the late epoch-0 observation, emit no later task press, and clean
up once. Healthy arms retain real task presses rather than disabling input.
The cleanup send/sync cells only obtain a verified receipt **after the harness
resumes the backend**, while the observation query is still blocked. Readback
failure does not trigger replay or a fabricated confirmation.

## What executed and what the evidence proves

Both arms call actual `X11Backend.key_state`, `pointer_button`, `release_all`
and their tracking/readback logic. Xlib injection, sync, keymap and pointer state
are memory-only doubles. The actor loop, observation proof, epoch, cancellation
publisher and fake expiry clock are probe-owned. No `NativeHandleBridge`,
`dispatch_in_session`, MCP endpoint, actual visual binding or process identity
lookup runs in this spike. The preceding [public-path A01](../public_guard_blocking_a01_20261015/RESULT.md)
remains the higher-level baseline; its results are not transferred here.

The ordinary/optimized runs each have two healthy and eight revoked cells.
They are deterministic finite schedules, not independent incident samples or
a reliability, performance or latency estimate. Python scheduling, the GIL,
memory recorder and backend availability remain assumptions. A five-second
harness escape is not an enforced release deadline. Fake event clocks are
logical markers; backend receipt timestamps are real monotonic values and are
not compared to the fake clock. Cancellation is published at a named blocked
query, not every possible in-flight press interleaving. A local gate is not an
atomic fence on later X-server acceptance.

`normal.json` and `optimized.json` preserve every case's events, owner identity,
prefix/terminal state, boundary snapshots, actual backend receipt/unknown and
pending cleanup obligations. Adjacent audit files bind the exact raw SHA256.
The auditor imports only the standard library. It replays key/button transport
effects and revocation epochs at snapshot/read positions, joins receipts to
their event order, and checks healthy-arm injection equality. This is independent
saved-data checking, **not independent OS or application sensing**.

## Construction and audit corrections before freeze

The initial empty-check auditor failed six hand-derived corruption tests.
Pre-freeze review then found that false boundary epochs, cleanup-before-revoke,
healthy release reordering and empty samples before release could pass. New
tests demonstrated four failures and then one further failure before the checks
were repaired. Publication/state transitions and their event records now share
a memory lock that is released before blocking cleanup. Actual backend receipts
remain unchanged; fake keymap/pointer samples are recorded separately and checked
against transport replay. Four test methods, including the ten schedule cells
and hand-derived negative controls, pass normally and optimized.

The first freeze command, invoked as a direct script without repository import
context, stopped at import before any freeze/output/case. Module invocation
resolved this without a source change. Frozen normal and optimized collection
each ran once; outputs refuse overwrite. No failed/native/live run was retried
or relabelled. `SOURCE_FREEZE.json` binds exact bytes of the selected materialized
checkout files, not every repository source; `POSTCHECK.json` records rehashes.

## Decision and next experiment

Retain this spike as evidence for moving blocking **observation** off the sole
input owner. Do not install a second cleanup connection or promote the prototype
to a runtime guardian. The supported guarded caller still synchronously reads
focus/process identity/capture on its path; this experiment does not fix that.

Next, integrate an explicit observation request/reply boundary into the selected
caller while preserving actual source association, generation, deadline, one
input owner and late-reply refusal. Test the same held-prefix cancellation and
expiry through that caller before live qualification. Separately qualify bounded
input send/readback and unknown recovery; thread separation cannot release input
through a stalled input transport by itself. Then require independent task
effect, finite recovery and matched efficiency evidence on fresh permitted live
attempts. #17 and the overall computer-control objective remain open.

## Reproduction

For saved evidence only (no X/runtime import), use fresh audit output paths:

```text
python -B research/live_control/fake_x_single_writer_spike_20261015/audit.py research/live_control/fake_x_single_writer_spike_20261015/normal.json --output REPRO_AUDIT.json
```

The producer is a Fake X construction. To rerun on exactly reconstructed frozen
checkout bytes, invoke it from the repository root as a module, with a fresh
output name. A checkout with different line endings/source hashes is a changed
source construction, not a replay of the frozen evidence:

```text
python -B -m research.live_control.fake_x_single_writer_spike_20261015.probe --output REPRO.json
```
