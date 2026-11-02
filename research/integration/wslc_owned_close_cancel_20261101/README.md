# Direct owner close during cancellation

The preceding change serializes concurrent cancellations, but direct
`OwnedGuardedSessionOwner.close()` previously closed the prestarted supervisor
without acquiring that cancellation transaction lock. A deterministic unit
test held the transaction lock and observed that the prior candidate closed
the supervisor and returned `closed` instead of declining the concurrent close.

The experimental change has direct close acquire that lock non-blockingly. If
the lock is held, close returns `busy`, retains UNKNOWN/no-replay semantics,
does not close the supervisor, and does not cache a closed report. The caller
must retry close after the active cancellation finishes. When the lock is free,
the existing close path runs under it; cancellation requests cannot overlap it.

In one WSLc private-Xvfb trial a real guarded owner pressed `a`; the harness
paused the first cancellation just before cleanup and invoked direct owner
close. Close returned `busy` and the prestarted supervisor remained alive.
After resuming, the first cancellation retained its operation identity, the
supervisor recorded `a` release readback, the independent target observed the
release, and a fresh guarded task succeeded. Overall old cleanup remained
UNKNOWN and replay disallowed. The pause is an injected race, not a failure rate.

The new unit test failed on the earlier candidate; 76 related tests passed in
normal and Python `-O` modes on this candidate. Test output, frozen trial
conditions, manifests and target receipts are in `raw.zip`. The conditions'
`draft_head` is an older ancestor; the manifest identifies actual source. One
test cookie was scanned in raw and hexadecimal form against packaged material;
authority files and private launcher commands are excluded. WSLc reported
that swap-limit enforcement was unavailable.

**Unresolved integration boundary:** the current MCP server shutdown helper
calls `owner.close()` before waiting for the cancellation executor and does
not retry if close returns `busy`. Therefore this candidate can leave close
unfinished during transport shutdown; the existing passing lifespan test does
not establish retry or final owner cleanup. Fix and verify that integration
before promoting this draft. Direct `retire` and other callers are not covered
by this lock. This change does not prove queue drainage, complete release,
exclusive display ownership, or a hard end-to-end deadline.
