# Collision addendum — Issue #4485

**Classification: `STOP_DUPLICATE_ALLOCATION_COLLISION`.** The evidence in this directory is not
an accepted scientific result for Issue #4485.

After the local run completed, a fresh GitHub read found the authoritative branch
`research/issue-3924-broker-orbstac-v2-20260926` at `6efffcd13c8e0f4c225f3f5673c8a3eee720a451`
and Issue comment `5846982300` freezing the same allocation ID and study path before its formal
execution. The authoritative freeze is based on main `67f1aedace0039d2ab8e4550becfaea78c50653c`,
uses fake SHA-256 `e6824182c55dd5dbe15024402ccd63dcaddaf4407e0634bce13e65bb98739aa0`, and specifies
a 1.0 s broker timeout with a 5.0 s external bound.

This additional local run used older main `21dd6a26dbd9f5cb4a6e11b1060902799a76a733`, a different
fake SHA-256 (`c9855dcc434b3bd52c9d1a5d35d0fadb72f338d2e7fefde11499f91ed849c64a`), and 0.2 s / 0.3 s
internal/external timeout bounds. Its raw SHA-256 is
`d149992af141530fe97a54821e7694879d4f6745bf6e0ad982a8bca728dacad2`; its timeout row was killed
by the outer watchdog at 303.3 ms without a broker receipt. The zero-exit mismatch is present in
these bytes but cannot be used as the Issue's allocation verdict.

Preserve this invocation and its hashes as a collision/chronology record only. Do not pool it,
substitute it, or use it to satisfy any Issue #4485 gate. No retry was made after discovery. The
Issue received a correction comment (`5847017395`) retracting the prior provisional result claim.

The collision arose because the intake branch search queried `4485` while the reservation branch
was named with predecessor number `3924`; the issue comments were not refreshed immediately before
launch. This addendum records that process failure without changing the authoritative branch or
any predecessor evidence.
