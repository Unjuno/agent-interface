# A01: synthetic normal release-batch UP-order trace

Status before run: corrected scope, source frozen; candidate NOT RUN. Base main: 69dd261430cb1ed875f5a76411c4a2a54777c114. This supersedes the overbroad V15-selector wording in the initial preregistration comment; that selector/wrapper is outside this candidate's dynamic test.

## H/T/D/C/U
- H: Executing the exact frozen release-batch backend v1 with the exact frozen transition-owner v4/v3 and input-owner v12/V10 sources, for two distinct keys held under one lease, yields reverse-order XTest KeyRelease calls, no query_keymap between those calls, then the backend's single input_state call. The two emitted rows bind to matching owner-thread receipts and final owned_keycodes is empty.
- T: One execution of exact backend v1 and owner v4/v3/v12 through a FakeXlib interface. The typed backend v2 parent is a minimal test shim that drives exactly two DOWNs then two reverse UPs; no exception branch, retries, real X server, application, game, model, or OS input.
- D: Ordered fake display/XTest/sync/query/call trace, owner records, actual backend-published release rows, post-batch owner state, final synthetic key set. Candidate and auditor SHA256 values are frozen in FREEZE.json.
- C: Five executable files copied byte-for-byte from main commit 69dd261430cb1ed875f5a76411c4a2a54777c114; exact source blobs recorded in FREEZE.json. Pinned python:3.11.9 linux/arm64 digest; container has no network, read-only root, bounded tmpfs/CPU/memory. FakeXlib and typed-backend parent are explicit shims.
- U: Dynamic test does not cover V39 CLI selector or V15 runner wrapper, real X11 semantics, production startup, live input/game/task effect, useful feedback, latency, recovery, or permission/lease availability. No live allocation is consumed or implied.

## One-shot protocol
Run candidate exactly once after this corrected preregistration is committed to this branch and Issue #59. Then run independent auditor exactly once against its captured raw JSON. If setup fails before candidate starts, record STOP and exact error; do not silently treat a retry as the same experiment. Once candidate starts, no A01 rerun. Adjacent release-error/non-neutral cases are excluded due #7847/#7858.

## Decision gate
PASS only if the raw trace and independent audit establish two distinct DOWNs; reverse UP injections; zero keymap queries between explicit UP injections; backend input_state call after both UP calls; two matching identity-bound owner receipts; completed rows with verified empty post-batch ownership; and empty final synthetic keys. Otherwise record FAIL (counterexample) or STOP (infrastructure/protocol failure). PASS is synthetic component evidence only.
