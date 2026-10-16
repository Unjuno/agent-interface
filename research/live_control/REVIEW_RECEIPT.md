# Terminal review receipt — 2026-09-13

The prior assistant recovery spent time guessing image filenames and searching logs
because observation sequence numbers do not always equal PNG filenames: exact-image
reuse is intentional. Candidate presentation_v2 adds a review field to each terminal
in compact mode, including the latest observation sequence/capture time, actual image
path/reuse flag, owning program and whether it belongs to this program. Missing or
prior-program observations are explicit. It also includes the matching local servo
outcome and terminal creation time in the runtime clock domain.

This is presentation only. Source events are archived unchanged; unknown/critical
events remain forwarded through the previous projection. The receipt does not acquire
a new image, refresh authority or imply semantic verification. Its timestamp is
historical at delivery, not a live clock measurement. Older local outcomes are cleared
on their terminal. It adds metadata bytes; no token compression is claimed.

interactive_v14 offers this through `--presentation compact`, retaining session16
for an isolated presentation change. Full mode and earlier entrypoints remain frozen.
This does not promote later experimental tracker candidates or fix their identity
failures. Both the source event stream and delivered stream remain available.

## Evidence

Replay of four existing corpora checks eight terminal receipts, including five reused
image references, exact source-event preservation and critical-event forwarding.
Separate checks cover absent and prior-program observations. This is a projection
check, not an asynchronous delivery/retention stress test.

In an actual assistant xterm episode, the assistant typed `t991018` and Return, then
used the terminal receipt's sequence 6 → image 003.png mapping directly to inspect
the result. It saw the expected text and SAVED title, then requested independent
evaluation, which passed. The task used one submitted program and one initial clock
query; there was no post-terminal image-path search. `audit_review_receipt.py` verifies
six exact reconstructed frames, source hashes, receipt mapping, source immutability,
release and final score. Process exit was normal; per-child attestation is absent.

This simple typing episode is not matched to the prior Inkscape recovery, so the
absence of a path lookup is a usability observation, not a measured task speedup.
Clock-query reduction, planner latency distributions and model-token accounting
remain unmeasured. Next compare an identical recovery with/without the receipt and
profile where planner/tool time is spent before changing authority time semantics.
