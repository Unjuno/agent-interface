# Bounded MCP cancellation-executor drain

The previous MCP close helper called `ThreadPoolExecutor.shutdown(wait=True)`,
which could wait indefinitely for a stuck cancellation. This candidate stops
new executor submissions with `shutdown(wait=False)`, waits at most the
configured drain interval for the cancellation futures registered under the
server's call lock, and calls owner close only once those futures are done. If
any remain pending, it returns `busy` with UNKNOWN/no-replay and does not call
owner close. A later call can retry after the pending operation finishes.

Two targeted tests use a real thread pool, including a blocked cancellation:
the helper returns busy without calling close, the future remains active, and
after release a retry closes. The initial red run fails because the prior helper
did not support this bounded-drain interface; it is not a timing reproduction
of the old helper. Updated close-order tests and the other related tests total
82 passing in both normal and Python `-O` modes; the separate MCP server suite
also passed 29 tests with `/src` as its working directory.

In one WSLc private-Xvfb trial, a real guarded owner pressed `a` and the harness
paused cancellation before cleanup. The helper's 150 ms drain returned `busy`
while its future and supervisor remained live and without closing the owner.
After the harness resumed cancellation, a retry returned a non-busy close
receipt preserving UNKNOWN; the target observed release and a fresh guarded
task succeeded. This exercises the MCP helper with a real executor and X11
owner, not a complete live MCP transport shutdown. The 150 ms is an injected
test budget, not a real-time performance claim.

The waiting interval is finite, but this is not a hard process-exit guarantee:
Python executor threads cannot be forcibly stopped and may keep running or keep
the process alive after `busy` is returned. The owner may still be active, so
no replay or new authority is granted on that result. A timed-out server
shutdown does not automatically schedule a future retry; the returned and
persisted `busy` requires a later owner of the lifecycle to reconcile it.
`owner.close()` itself, pipe calls, and OS scheduling remain outside a proven
hard bound. The correctness of the future snapshot depends on the existing
server rule that shutdown forbids new cancellation admissions.

Conditions, source hashes, red/green results, target events and raw receipts are
included. The conditions' `draft_head` is an earlier ancestor; the manifest
identifies the candidate. One test cookie was checked in raw and hexadecimal
form against packaged files; authority files and private launcher commands are
excluded. WSLc reported no swap-limit enforcement.
