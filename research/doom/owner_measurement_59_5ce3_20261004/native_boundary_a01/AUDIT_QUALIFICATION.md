# Independent audit qualification (no rerun)

Reviewer Lorentz / 01a1038d-9b1d-7c13-a096-1033a3b493dd, read-only audit of
dc070a7dc protocol/runner and retained receipts (later committed75067dc5c).
This is a coordinator summary of the returned review, not an exact-head merge
vote. Reviewer performed no native/model/container replay or file/Git writes.

Critical: none. Important: two protocol gaps.

1. run_native.py88–91 retains only tested a/b/c empty, BEFORE close109.
   It discards the full bitmap and does not observe close-time events. The
   protocol's complete final-empty requirement is NOT established.
2. Imports/source reads/instrumentation13–25 precede protected execution;
   teardown119–127 or outer timeout can bypass RESULT serialization129.
   Successful retained run unaffected, but unconditional failure-retention
   promise is NOT established. Exclusive RESULT creation is not attempt reservation.

Reviewer independently confirmed exact RESULT/runner hashes, source owner/Lease/
Executor bytes, statically reconstructed measured bytes, all4 six-event traces,
foreign-up refusal, explicit-up None, verified release/close and stopped owners.
Both measured cells' identities/timestamps, chronological ordering, caller
containment and shared cleanup completion pass raw-data inspection. Local Git
protocol chronology precedes container startup, not independent timestamp attestation.
Terminal exit0/noOOM/offline/read-only/timeout and nonfatal Xvfb warnings checked.

Minor: runner assertions do not enforce full cross-operation ordering/containment;
runtime receipt omits selected builder/dependency/protocol hash custody;
read-only binds do not freeze backing files against host mutation. Current raw
records pass stronger ordering checks, but missing custody cannot be retrofilled
as historical runtime evidence. Workspace receipt commit advanced during review;
reviewed protocol/runner and supplied result hashes stayed identical.

Disposition: retain raw PASS_NATIVE_OWNER_COMPONENT unchanged; independently
supported scoped component execution, but HOLD_COMPLETE_PROTOCOL_REQUIREMENTS.
Not all protocol gates passed. Reviewable as qualified evidence only, not runtime
adoption, full release certificate, useful task effect, speed or game qualification.
Missing post-close/full bitmap evidence cannot be recovered from this raw packet.
Any stronger experiment requires a separately frozen successor, not A01 retry.
