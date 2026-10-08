# Native owner loss between effect and reply

2026-09-20. The primary assistant used the existing native exchange to move and
save a shape in a fresh private Inkscape session, then an injected checkpoint
stopped the harness immediately before publishing reply-1.json. An external
supervisor verified PID plus Linux starttime and stopped state, sent SIGKILL,
and observed terminal state. No request was replayed to repair the missing reply.

## Observed problem and shared change

In run-1, nine Right chords after the scoped 50 ms selection wait saved x=68.
The client timed out with pending. After the owner was killed, two read-only
resumes still returned pending. The saved SVG proved effect despite no reply.
The directory-fsync change was already present; owner identity was not yet
recorded. This is a diagnostic pre-fix run, not a matched performance baseline.

The private desktop harness now publishes owner.json before application setup.
It identifies the process by PID, starttime, boot ID and PID namespace. When no
reply exists, the exchange checks that local incarnation. A live or SIGSTOPped
owner can remain pending; timeout alone never establishes death. An absent,
replaced or terminal incarnation produces unknown_requires_external_reconciliation.
Foreign/unreadable/malformed identity also requests reconciliation, with an
unverifiable reason rather than a death claim. The response explicitly leaves
emission and release unknown and grants no input authority.

An already committed, correctly correlated reply takes precedence over owner
state. Historical runs without owner.json retain bounded pending behavior.
This local /proc diagnostic is not a distributed lease, owner takeover or
restart protocol. No automatic action replay, release or owner restart is added.

## Fresh primary use with the change

Run-2 used seed 991089, five Right chords and the same scoped selection wait.
The primary assistant viewed the initial image, submitted one action, and saw
pending while the checkpoint had stopped the still-existing owner. After the
supervisor killed that exact process, two independent CLI resumes returned
unknown_requires_external_reconciliation / owner_process_absent.

The supervisor queried the private X server through a separate connection:
keys_down was empty and pointer mask was zero in both runs. It copied and hashed
the live saved SVG after owner death: x=68 in run-1 and x=60 in run-2, with y=50,
width=40, height=30 and no transform. The primary assistant also viewed each
already-published source-2 image; these historical captures agreed with the
saved geometry. They were not substituted for the missing reply.

An explicit duplicate submission in run-2 raised FileExistsError. Starting the
normal harness with that same output directory also refused before GUI setup.
All existing artifact bytes were unchanged by these controls; exactly one native
program file remains. Program files and backend counters are producer records,
not an independent complete X input event trace. The separate X connection
establishes neutral state only at its observation time.

Both owner command handles became terminal (exit 1 from the WSL command wrapper;
SIGKILL was requested and independently checked). Their remaining private app,
WM and Xvfb processes were explicitly terminated by PID/starttime-checked cleanup.
Absent/zombie states are terminal, not proof of clean application shutdown.

## Publication durability prerequisite

publish already fsynced complete file bytes before an exclusive hard link.
It now fsyncs the containing directory before returning. A directory-sync error
after the link leaves a complete occupied slot and propagates an error; the caller
must inspect it read-only, never infer that no request was committed. Removing
the temporary alias is cleanup; a storage crash may leave an orphan temp alias.
Unsupported storage fails rather than silently claiming a durable publication.

Directory fsync succeeded on this WSL workspace. This establishes use of the
filesystem primitive, not power-loss durability of the Windows/WSL storage stack.
No host reboot, power cut, store loss or filesystem-corruption experiment ran.

## Validation and limits

43 focused bridge/exchange/presentation/reference tests passed. Added cases cover
file-sync/link/directory-sync order, occupied-slot behavior on injected sync
failure, live/replaced/stopped/zombie owner, foreign/malformed context and
committed-reply precedence. The retained audit checks 32 image hash links, request
correlation, external saved-file hashes, controls and terminal cleanup.

This addresses an actual recovery-status gap while preparing Issue #2704.
It is NOT PASS_NATIVE_EXCHANGE_CRASH_SAFE_REPLAY_SCOPED: the six prescribed crash
positions, a private Calc allocation, missing/corrupted durable stores, independent
complete event ledger and restart/reconciliation protocol remain untested or
unimplemented. Exactly-once emission, safe automatic replay, crash-time input
release, performance, model tokens and production reliability are not established.
Helper model calls were zero; model usage is unavailable.

Raw runs are additive; source holds final executed source and supervisor scripts.
Run-1 used the base harness plus the directory-sync change; its intermediate
native_exchange source was not separately snapshotted. Base commit:
ede35c0c891f0255d266aff0529a876b5c73ddc6. Original absolute paths remain provenance;
archived PNGs can be located by filename. SHA256.json covers all retained files
except itself. No frozen benchmark or old evidence was modified.
