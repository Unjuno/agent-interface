# Recovery review: Issue #3934 source freeze and formal PASS record

This path preserves the exact five-file source/freeze snapshot from old branch
`research/issue-3934-scheduler-other-cpu-20260922` at
`4489206e9652ccce269b8d0a0c0597f196de8353`. Its source files are unchanged.

## Formal result boundary

Issue [#3934](https://github.com/Unjuno/agent-interface/issues/3934)
comment [5766288105](https://github.com/Unjuno/agent-interface/issues/3934#issuecomment-5766288105)
records one completed Linux-container timing invocation and
`PASS_SAME_CORE_ATTRIBUTION_SCOPED`: 30 triplets, 90 blocks and 27,000
timestamps; no retries, replacements or exclusions. It reports the frozen
tail-attribution gates and a successful independent raw-only audit.

The same comment explicitly says the 66,132-byte lossless raw archive (claimed
SHA-256 `a24f98a4b0c6f1e43c0eddbdcf8255f6ad4e8206a02a613c8f207668a8593c53`)
was still being assembled and full remote retention was not yet claimed. It
is absent from the recovered branch; the reported first audit JSON is absent
too. This recovery therefore preserves the frozen sources and Issue-level
result record, but **does not recover or independently verify the formal raw
timing rows**. The separate posthoc review in merged PR #4072 is not a
substitute for those rows and is not conflated with this PASS.

No timing blocks or formal auditor were rerun. The original allocation is
consumed; retain the result only at its stated synthetic Linux-container
scope. No X11, model/task utility, physical-host isolation, hard-real-time, or
runtime-promotion claim follows.

## Local recovery checks

The original frozen construction suite includes Linux-only CPU-affinity and
`sched_getcpu` calls. On this macOS host the test module stops during import
because libc does not expose `sched_getcpu`; no Docker image was frozen for
the original allocation. This is an environment STOP, not a changed formal
result, and the construction/formal allocation was not rerun.

The recovered `SOURCE_BUNDLE.json` claims `gzip+base64` and payload SHA-256
`57ec36ab533f3c5fd4eff57b684aa2e2fed268af5963f1c73e55bd416cabda35`, but its
encoded bytes fail gzip decompression (`invalid distance too far back`). The
separate `run.py`, `audit.py`, `test_study.py`, and embedded metadata remain
preserved exactly. Do not claim that the bundle payload or missing timing
archive was restored; the original source freeze hashes are checked separately
against the retained standalone/embedded file bytes.
