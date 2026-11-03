# Retiring the private display after owner death

In this WSLc harness the real guarded owner pressed `a` on an independent
target and was deliberately terminated while the key was down. Cancellation
returned `cancel_unconfirmed`, preserved the `a` obligation, left cleanup
UNKNOWN and disallowed replay. The harness then compared two fixed-order paths:

| Path | Treatment of old held key | Fresh task |
| --- | --- | --- |
| Retire private display | No fixture key release; terminate and reap the exact Xvfb owned by `PrivateDisplayOwner` | Start a fresh private display and target; guarded `a` effect and release observed |
| Keep private display | Harness sends a fixture `a` release | Start a fresh target on the same display; guarded `a` effect and release observed |

In both trials an independent keymap showed `a` down before the intervention
and the fresh target received `a` and its release; the fresh display was neutral
afterward. The old target exited 1 in the retired-display arm because its X
server was killed; the fresh target exited 0. Both Xvfb processes were reaped.
The old operation's task success and physical release remain unknown. Killing
the old X server removes that server's state; it does not prove that a key-up
event reached the old application or that queued requests were drained.

This is a harness-orchestrated recovery experiment, **not** a production
implementation: cancellation and private display retirement are still separate
APIs, and the caller must already own the entire disposable display. It shows
a candidate route to finite recovery, with data loss in the retired environment,
not a general recovery guarantee or a hard latency bound.

The first retirement attempt stopped after successful old-server retirement
because the test helper failed to restore its parent `XAUTHORITY` before an
assertion. Its output is preserved as `initial-failure`; the corrected pair
used new allocation names and is preserved as `controlled-pair`. No result is
rewritten or combined into a reliability estimate. Pinned image, CPU/memory and
network settings, hashes, target events, and receipts are in the source
manifests, conditions and `raw.zip`. Five test cookie records were checked in
raw and hexadecimal form against packaged files; authority files and private
launcher commands are excluded. The environment did not enforce swap limits.
