# Evidence-gated deferred owner close

When MCP close times out waiting for tracked cancellations, the server retains
the initial `busy` report and arms a one-shot callback for those futures. Once
all have actually finished, a daemon thread attempts a separate deferred close
and writes a separate `session-…-deferred-close.json` report. Repeated arming
does not create duplicate attempts. A close exception is recorded as UNKNOWN.

The deferred owner method acquires the cancellation transaction lock and only
enters the existing close path if the old owner is confirmed retired and both
its disconnect and prior release-attempt records exist. Under that condition
the existing close path preserves the old receipt instead of issuing another
release. If that evidence is missing, or the lock is busy, it records `busy`
and does not invoke close. This avoids treating future completion itself as
proof of release or as authority to send a late key-up to another client.

In one WSLc private-Xvfb trial, a real guarded owner pressed `a`; cancellation
was paused before cleanup and bounded close returned `busy` with the future
and supervisor still live. No deferred result appeared while the future was
pending. After resumption, the guarded owner retired, the independent target
observed `a` release, and the deferred close wrote a separate `cleanup_failed`
receipt preserving UNKNOWN/no-replay. A fresh guarded task then succeeded. The
test exercises the actual X11 owner and helper with an injected pause, not a
full live-GUI MCP transport shutdown.

Four focused unit tests cover all-futures completion, one-shot scheduling,
exceptions, and refusal without retired-owner evidence. Together with existing
tests, 86 tests passed in both normal and Python `-O` modes. A subsequent MCP
lifespan test deliberately blocked cancellation-archive persistence beyond the
drain interval; it verified the initial `busy` file remained intact and the
separate deferred result appeared after release. That new lifespan test passed
in both modes; it uses the fake-X fixture, not a live GUI. The separate MCP
server suite passed 29 tests. The 86-test run and live manifest predate the
addition of the lifespan test; the post-test source manifest is separately
recorded and the production candidate is unchanged between them.

This is eventual, evidence-gated work, not a hard process-exit guarantee.
Executor threads and the close call may still block, and the daemon can be
terminated when the process exits before writing a deferred result. If the
future never finishes, evidence is missing, the close stays busy, or the write
fails, no completed close is guaranteed; a write failure is retained only in
memory. The old task, physical release guarantee, and queue drainage remain
UNKNOWN, and production private-display integration is still absent.

Conditions, hashes, test output and raw receipts are retained. The live
conditions' `draft_head` is an older ancestor; manifests identify actual source.
One test cookie was checked in raw and hexadecimal form against packaged
files; private authority and launcher commands are excluded. WSLc reported no
swap-limit enforcement.
