# Private-display recovery: late receipts

The experimental controller previously treated a late `cancel_requested`
receipt as completed and could permit a fresh display when retirement returned
after the transaction deadline. Two deterministic unit tests reproduced these
cases against that candidate. The change checks the absolute monotonic deadline
after cancellation and after display retirement. Late results remain recorded,
but recovery is UNKNOWN and a fresh display is not authorized. A malformed
display-retirement receipt is also classified UNKNOWN.

This is **receipt fencing**, not a hard wall-clock bound: the coordinator calls
the guarded owner and display owner synchronously, so a blocked underlying call
can still delay return past the deadline. An already-retired display may be
recorded as retired after the deadline without authorizing a replacement.
Task success, release confirmation and replay remain unclaimed.

On the final candidate, 73 related tests passed in normal and Python `-O`
modes. The added late-receipt tests use a controlled clock; they are not real
timing measurements. One separate WSLc trial repeated actual guarded `a`
delivery, injected owner death, controller-led private display retirement, and
a fresh display task with independent target effect and release. It passed;
old cleanup remained UNKNOWN. This does not establish production MCP
integration, exclusive custody, queue drainage or a real-time guarantee.

The trial harness, source manifest, red/green test output and raw receipts are
included. The conditions' `draft_head` is an earlier source ancestor, while
the manifest records actual candidate hashes. Two test cookie records were
scanned in raw and hexadecimal forms against the archive; authority files and
private command paths are excluded. WSLc reported no swap-limit enforcement.
