# A02: synthetic normal release-batch UP-order trace

Successor to A01, which is preserved as STOP before candidate startup due to an outer command-quoting error. A02 changes only the frozen invocation wrapper and package paths; the candidate/auditor test objective remains the corrected scope below. No candidate has started.

## H/T/D/C/U
- H: Executing the exact frozen release-batch backend v1 with the exact frozen transition-owner v4/v3 and input-owner v12/v10 sources, for two distinct keys held under one lease, yields reverse-order XTest KeyRelease calls, no query_keymap between them, then the backend's single input_state call. The two emitted rows bind to matching owner-thread receipts and final owned_keycodes is empty.
- T: One execution of exact backend v1 and owner v4/v3/v12 through FakeXlib. A minimal typed-backend-v2 parent shim drives exactly two DOWNs then two reverse UPs. No exception branch, retries, real X server, application, game, model, or OS input.
- D: Ordered FakeDisplay/XTest/sync/query/call trace, owner records, backend-published release rows, post-batch owner state, final synthetic key set. Candidate, auditor, runner, and source SHA256 values are frozen in FREEZE.json.
- C: Five executable files copied byte-for-byte from main commit 69dd261430cb1ed875f5a76411c4a2a54777c114, with source Git blobs recorded. Pinned python:3.11.9 linux/arm64 digest; network none, read-only root, bounded tmpfs/CPU/memory. FakeXlib and typed-backend parent are explicit shims.
- U: Dynamic test does not cover the V39 CLI selector or V15 runner wrapper, real X11 semantics, production startup, live input/game/task effect, useful feedback, latency, recovery, or permission/lease availability. It consumes or implies no live allocation.

## One-shot protocol
First verify package SHA256 values with frozen runner.py. Then run runner.py exactly once in the pinned container. It starts candidate.py once and, only if candidate returns valid raw JSON, starts audit.py exactly once over that immutable stdout. If package verification or setup fails before candidate starts, record STOP; do not rerun A02. If candidate starts, no A02 rerun. Adjacent release-error/non-neutral cases are excluded due to #7847/#7858.

## Decision gate
PASS only if the raw trace and independent audit establish two distinct DOWNs; reverse UP injections; zero keymap queries between explicit UP injections; backend input_state call after both UP calls; two matching identity-bound owner receipts; completed rows with verified empty post-batch ownership; and empty final synthetic keys. Otherwise record FAIL (counterexample) or STOP (infrastructure/protocol failure). PASS is synthetic component evidence only.
