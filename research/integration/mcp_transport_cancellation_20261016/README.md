# Public MCP cancellation while input or release transport is blocked

2026-10-16 JST. Base `ebc69919951948b67dc8d40448869078a8bee682`;
tested code `a1a58e3edad8cba8988ab48eea99d46738c4b6ad`.
Decision: **RETAIN_PENDING_TRANSPORT_CUSTODY_BOUNDARY**.
No runtime behavior/default changes. Five methods are registered once in protocol.

## Actual path and question

The [compiled observation-worker check](../compiled_observation_cancellation_20261016/README.md)
showed cleanup independent of a blocked read-only callback. This probe moves the
barrier into the single input owner's press/release transport. Does selecting
process, query and observation workers make a cancellation acknowledgement a
release confirmation, or stop an already-entered send from later arriving?

Actual in-process `create_server` / public FastMCP `call_tool` → serialized worker
→ GuardedSessionOwner → NativeHandleBridge → runtime session/backend. Both query
and observation workers are explicitly enabled, with process identity. Existing
FakeX owner and separate read-client fixtures replace platform/backend setup,
capture/XTest transport, keymap and process reads. The barrier is inside the fake
input send or fake owner-connection sync, not an extra input writer. This is not
stdio/network transport qualification. No display/input, provider/model,
WSL/container or formal allocation was run.

## Five cases per normal / actual optimized mode

| Barrier | Fake bitmap while blocked | Backend tracked ledger | Public result before resume |
|---|---|---|---|
| CTRL press send, before fake emission | Empty | CTRL | Pending; cancel accepted, release unconfirmed |
| CTRL press sync, after fake emission | CTRL | CTRL | Same |
| Cleanup release send, before fake emission | CTRL | CTRL | Same |
| Cleanup release sync, after fake emission | Empty | CTRL | Same |
| Stable selected worker route | No barrier | Cleared after readback | Completed chord, verified fake cleanup |

Release cases induce an independent process-generation change after CTRL press
to force cleanup before `a`; cancellation then arrives during that cleanup.
Press cases cancel while their original transport call is in flight. Each
blocked row retains an entered Event, unfinished gate, live worker thread ID,
same-call pending lookup, actual fake bitmap and tracked backend ledger. Repeated
cancel is acknowledged as already_requested, does not renew the original lease,
and does not inject cleanup. New input, close and recovery all return busy while
that worker owns the slot. No second writer or automatic replay starts.

After explicit barrier resume, the original call returns execution_failed with
verified fake cleanup. Final emissions are only CTRL press/release, no `a`.
Retrieval uses the same original call ID. A later cancel is not_active and old
alias input is refused under review. The stable control emits one complete
CTRL+a chord. All fake key state and backend ledgers finish empty; owned read
threads are closed and joined.

Two distinctions are decisive:

- In press-send, the CTRL press arrives **after cancellation acknowledgement**,
  when the already-entered transport call resumes. The late-press fence ran
  before that blocked send; it cannot unsend an in-flight request.
- In release-sync, the fake bitmap is empty **before cancellation acknowledgement**,
  but no verified release result is available while sync remains blocked. The
  backend ledger still retains CTRL until readback completes.

Host-monotonic event order is retained. Test barriers/watchdogs and fake bitmap
reads are not physical latency bounds. The initial pending response explicitly
has release_confirmed=False/effect_status=unknown. Retained pending lookup does
not supply release_confirmed on this source; its absence is not treated as a
positive confirmation or zero-input claim. operation_invoked=False on lookup
describes the read operation, not the original in-flight input call.

## Verification and custody

The affected selection passes **60 modules / 449 unique methods**, zero
failures/errors/skips, in normal and optimized Python. It includes existing
guarded MCP, recovery and interruption-receipt tests plus the prior compiled
selection; it is not every native/platform suite. No production change was
needed to obtain these results. Initial local test construction assumed a
release_confirmed key on pending lookup and raised four KeyErrors; the test was
corrected to preserve the actual absent/unknown shape before the pinned runs.
Those initial console errors were not retained as a separate full raw packet.

97 selected source/data joins were recorded before execution. Five supplemental
MCP implementation joins were checked afterward at the unchanged tracked HEAD;
[SUPPLEMENTAL_SOURCE_PINS.json](SUPPLEMENTAL_SOURCE_PINS.json) makes that timing
explicit. Neither selection is a complete dependency closure. CONDITIONS' base
is the tested code; inherited old_prs metadata is historical navigation only.
Both full record archives, exact retained call files as hex, conditions, process
IDs/optimization flags and complete stdout/stderr are preserved.

The saved-only reader joins same-call native release reports, checks both
in-flight distinctions, late-press event order, pending/duplicate/busy/terminal
outcomes and six copied contradictions in each mode. It imports no candidate
and scores no application. Runner/reader `.py.txt` files are inert references
with their original local path bindings.

## Decision and next boundary

Reuse the existing pending-call custody and serialized refusal; do not advertise
query/observation isolation as input-transport preemption. Bounded response wait,
cancel acknowledgement, fake neutrality and verified release are separate facts.
A finite physical-release claim needs a specified, qualified input/release
transport or server-side authority bound. Another read-only worker, response
timeout, replay or parallel writer does not provide that bound. Until qualified,
retain unknown custody and the original call rather than reopening another
writer. Native blocked I/O/server stalls, process-death custody, independent app
effects, finite semantic recovery and matched economics remain open. Keep
#17/#59/#57 open; preserve the earlier component PASS and these residuals.
