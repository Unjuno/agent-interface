# Owned cancellation control-lock deadline

The owned guarded session previously waited without a bound for its control
lock. A regression test held that lock beyond a 50 ms cancellation deadline:
the old code remained blocked until the test released it. The candidate bounds
lock acquisition by the remaining absolute deadline, rechecks before sending,
and limits control-response polling to the remaining time. If the lock cannot
be acquired, it sends no cancellation signal, marks the result UNKNOWN, requires
review, and disallows replay. The cancellation signal's `input_dispatched`
field does not describe the original guarded action.

In one separate WSLc trial an actual guarded owner pressed `a` on an independent
target and paused; the harness held the owner's control lock and requested
recovery with a 200 ms deadline. The call returned after approximately 200.2 ms
with `control_lock_deadline`, no cancellation signal, no fresh-display
authorization, and `a` still down. The harness then retired the old owner and
private display as fixture cleanup; a fresh display task produced an independent
`a` effect and release. This single observation is not a latency guarantee.

The new regression failed on the prior candidate and 74 related tests passed
on the candidate in both normal and Python `-O` modes. Source manifests,
conditions, red/green outputs, target events and raw receipts are included.
The conditions' `draft_head` is an earlier ancestor; the manifest hashes the
actual candidate. Both test authority cookie records were scanned in raw and
hexadecimal forms against the archive; authority files and private command paths
are excluded. WSLc reported no swap-limit enforcement.

This only bounds the lock and the poll wait. Pipe `send`/`recv`, process
retirement, cleanup and scheduling are not established as a hard end-to-end
deadline; a timed-out lock does not prove that another in-flight operation has
stopped. The trial's fixture teardown is not automatic production recovery.
Shared per-owner cancellation state and concurrent completion still require
separate analysis before this draft can be promoted.
