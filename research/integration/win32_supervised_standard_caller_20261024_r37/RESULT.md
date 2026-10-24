# R37a — input-free preflight stop

**Disposition: `FAIL_OR_UNKNOWN` setup stop; no formal phase ran.** The first
preflight invocation failed before input because `run_r37.py` and
`preflight_r37.py` selected a parent directory outside the Git worktree. The
retained `preflight.json` records the `git rev-parse HEAD` failure and
`native_input_sent: false`. No fixture, hook, dispatch, cancel or task ran; this
did not consume a live allocation.

The root calculation was repaired in sibling packet
[R37b](../win32_supervised_standard_caller_20261024_r37b/RESULT.md), which uses
a new attempt ID, new task token, and its own frozen source hashes. R37a's
preflight output and source packet remain unchanged. SHA-256 checksums cover
every file in this packet except `SHA256SUMS` itself.
