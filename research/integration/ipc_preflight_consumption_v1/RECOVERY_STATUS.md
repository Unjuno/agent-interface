# Recovery status for #3987 outer-preflight allocation

The original `FREEZE.json` is preserved byte-for-byte (SHA-256
`8e0016d90e09afa7aee7146070bf8f49c8c4b33a9528746bfc10247beac4dafb`). It
identifies allocation `outer-preflight-exit-20260922-01`, a separate 12-case
outer-preflight/caller study.

The Issue reports `PASS_PREFLIGHT_COMPLETION_BOUNDARY_SCOPED`, one invocation,
12 completed case pairs and outer exit 0. However, the old branch contains only
the freeze. Its runner, environment, plan, source, raw rows and audit package
are absent both here and from current main, so this recovery cannot reproduce
the reported result. Do not treat the Issue summary as byte-level raw
verification.

The merged PR #4022 publishes the distinct 24-stream
`ipc_completion_join_v1` study. It is not a replacement for this 12-case
allocation and is not used to validate it.

Disposition: `HOLD_REPORTED_PASS_PACKAGE_MISSING`. No rerun or reconstruction
was made. The allocation remains historical and unverified; the original
freeze is retained so a future owner can locate the exact intended sources and
raw artifacts.
