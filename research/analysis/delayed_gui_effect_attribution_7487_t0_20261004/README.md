# Issue #7487 T0 — delayed GUI-effect attribution fixture

This package is a no-participant method experiment. It tests only whether a
small synthetic source ledger can be rendered at two display delays in two
formats without changing event facts, fabricating causal links, or erasing
`UNKNOWN` provenance. It does **not** measure human attribution accuracy or
test a GUI, model, application, retry decision, or product behavior.

The five frozen traces cover agent-caused, human-caused, delayed unrelated,
overlapping-action, and genuinely unknown/conflicting effects. Each is crossed
with 300/1500 ms display delay and chronological-summary/source-bound-receipt
presentation (20 records). Summary and receipt are alternative renderings of
the same ledger; only receipts expose the ledger's declared source relation.
The receipt renderer reads that relation, never infers it from timestamp
proximity. The `UNKNOWN` trace has two competing actions and no declared link.

## Execution boundary

OrbStack was the required preferred isolated runtime on this macOS host, but a
read-only `docker image ls` failed in the daemon while opening a cached
containerd blob (`operation not supported`). No image pull, build, daemon
restart, or second daemon inventory attempt is authorized or performed. This
is retained as `STOP_ORBSTACK_DAEMON_BLOB_READ`; the finite, standard-library
fixture is separately run host-only as an explicit portability exception. The
host run is not container evidence and does not claim isolation or resource
enforcement. No human study is authorized by Issue #7487.

See `FREEZE.json` for the source/base identity and preregistration boundary;
`RUN.md` for exact invocations and raw hashes; `REPORT.md` for the scoped
outcome. Candidate and auditor run at most once each after the source freeze.
