# Current strict-owner RPC v2: retained socket/Fake X evidence

Base main `540fdfe85b7a3b8c863b22fe91808f3213a51f31`,2026-10-16. This repairs the
codec/client gaps reproduced in the [#8876 convergence](../crash_owner_convergence_20261016/README.md)
by adding an explicit current-owner socket service, without installing the old
process adapter or changing default callers. [API and limitations](../../live_control/INPUT_OWNER_RPC_V2.md)
define the supported construction boundary.

H: the original process/window source and same-intent authority survive a
versioned wire copy, and any uncertain reply stops further sends on the same
client. T: real local `socket.socketpair()` between client/service threads and
actual current selected backend/transition owner/InputOwner v12, with all X11,
focus/process query and capture replaced by the existing Fake X fixture. The
codec preserves window source but service admission explicitly refuses it.
D: original binding reaches native admission; changed identity/lease, duplicate
ID/JSON members and malformed local input cannot cause second input; uncertainty
and incomplete owner cleanup never become verified release. C: healthy bound
input/close, explicit cancel and autonomous generation/expiry provide controls.
U: no external process, native X server, physical input, clock-transfer, default
session/Executor, durable recovery, application effect or efficiency result.

## Final checks

[verification/normal.json](verification/normal.json) and
[verification/optimized.json](verification/optimized.json) each retain **41 methods
in5 modules,0 failures/errors/skips**, including16 new RPC methods and26 socket/
codec/Fake X rows. Each mode records46 LF-normalized source pins. Dedicated local
Python3.13.14, Pillow12.2.0, numpy2.3.4 and python-xlib0.33; Windows sockets and
threads only. Final commands used `python -I` / `python -I -O` with the preserved
`exploratory/check_owner_rpc_v2.py.txt` driver and additive external output paths.
Its fixed workspace path identifies the actual test setup, not a new dependency.

| Boundary | Retained discriminator |
|---|---|
| Source/intent | JSON roundtrip retains process/window tuples and original deadline; cancel remains sticky; same-token rebind rejects. Current owner admits the bound process source and refuses a stale generation. |
| Replies | Dropped reply, wrong ID, malformed record list and partial frame occur after fake key38 is admitted. Same client's second down sends nothing; local close is unverified; separate server EOF receipt records stopped/empty cleanup. |
| Server protocol | Duplicate request ID, changed same-intent source and duplicate JSON member close before a second press. Fake mapping also supports keyd/code40, so refusal is not an unavailable-key artifact. |
| Readiness / pre-send | Wrong service ID and integer1 in place of boolean capability reject. Missing/expired local sources and unsupported window source do not consume input request identity; a subsequent valid control can proceed. |
| Active owner | While RPC is idle, generation change and original deadline release held input; explicit cancel is carried in an `input_state` update. This does not imply automatic parent cancellation or asynchronous event delivery. |
| Close | Successful raw close retires the same client. Contradictory stopped/verified fields and KeyboardInterrupt yield no local verification; primary interruption remains visible and repeated close keeps its unknown result. |
| Blocked native release | Client close times out; service owner-close also returns with owner thread still blocked and fake key38 held. Both receipts remain unverified. Resuming the fixture later releases input, without rewriting the earlier receipt or proving a physical bound. |

Rows record framed **send attempts** and Fake X edge observations, not a guarantee
that every attempted frame was delivered (e.g. a cleanup attempt after deliberate
peer EOF). There is one serialized client writer and one service per socket.
Fake X native owner runs on its own thread; service/client are in the same OS
process. The service's returned receipt is retained by the harness; it is not
fsynced by the service and does not survive host/supervisor failure on its own.

[Independent readback](read_saved_rows.py) checks all26 rows, source pins, wire
identities, original native-admission source, single post-uncertainty input,
release/stop distinctions and protocol controls. It rejects10 altered records
per mode; [READBACK.json](verification/READBACK.json) preserves the outcome.
A separate candidate mutation removes only `call`'s sticky quarantine assignment.
The four-fault test rejects it with **3 assertion failures and1 partial-frame
parse error** after the forbidden second send. This negative was run before the
later constructor capability-type and buffered-reply/teardown repairs; it is
retained as historical construction evidence. It is not a native performance/control experiment.

## First results and repair history

All first streams, available exact source/test versions and mutant source/driver
are retained under `exploratory/`; none are formal allocations. The absent module
first failed one assertion. Initial7 RPC methods passed; additional checks then
found a contradictory close receipt was accepted (one failure), an interrupted
close lost its repeatable unverified result (one failure), numeric readiness
capability1 was accepted as booleanTrue (one failure), and generic fatal close
exceptions/fatal groups were wrapped and suppressed (two failures). Each was repaired before
final verification. Initial and intermediate passing outputs are construction
history, not final-source verification. Some intermediate passing test revisions
were enriched in place before a separate source copy was made; source hashes
remain in those reports when collected, but only final modes are qualified by
current source/readback. The first source, close-red test and pre-interrupt/
capability-red source+test pairs are retained where available. No old live
producer or consumed allocation was replayed.

## Adoption and next connection

Adopt the explicit library and regressions, not a default desktop/game path.
The old RPC counterexamples are repaired at this service boundary; blocked
native release still remains unknown. Follow#59 with an externally supervised
service process and durable receipt, an actual selected-backend adapter that
preserves unknown cleanup custody, cancellation/telemetry propagation and then
session/controller death checks. Window observer transfer must keep its canonical
epoch; physical release time, independent task effects and matched resources
remain unproved. Existing session/controller selection is unchanged.

Review follow-up: initial immutable commit ddb194cb702455b1c4ab04815cca9af4e60c8c00
passed39 selected methods but a reviewer reproduced primary KeyboardInterrupt
being replaced by socket-close OSError. Paired readiness/client/service teardown
now retains both objects in BaseExceptionGroup, with repeated client close still
unverified. A coalesced extra-response construction also showed the old client
accepting a valid first reply despite buffered unsolicited bytes; it now
quarantines before any next request. The combined red had1 assertion failure
and2 cleanup errors, followed by1 service cleanup error; exact sources/tests
and streams are preserved. Final verification above is the repaired41-method,
26-row version. Service-preflight validation occurs before ownership acceptance;
if preflight raises, the supplying caller retains cleanup responsibility.

Final-source negative control: `exploratory/owner-rpc-v2-reviewed-quarantine-mutant.*`
removes only the post-send exception handler quarantine assignment. Three fault
subtests fail assertions (0 errors); the partial-frame subtest still passes
because the new independent buffered-byte fence blocks its second send. Source
and driver are retained separately from the earlier3-failure/1-error negative.
