# MCP close retry after cancellation executor drain

The prior experimental owner close returns `busy` while a cancellation owns
the transaction lock. The MCP shutdown helper formerly wrote that `busy` result
and then waited for the cancellation executor without trying close again. The
candidate preserves the first close attempt and executor shutdown, but if the
first report was `busy`, it attempts close once more after the executor has
drained and persists the final report. A second `busy` remains `busy`; there is
no unbounded retry loop. If the first close raises, executor shutdown is still
attempted and the exception remains visible.

Five targeted tests cover ordering, normal close, a still-busy result, exception
handling and a real thread-pool drain. In one private-Xvfb WSLc trial a real
guarded owner pressed `a`, its cancellation was paused before cleanup, and the
same MCP close helper was called with the actual cancellation executor. The
helper waited while the supervisor remained alive; after the injected pause was
released, cancellation finished, close retried and returned `cleanup_failed`
with old cleanup UNKNOWN rather than `busy`. The independent target observed
`a` release and a fresh guarded task succeeded. This exercises the MCP helper
and real owner, not a full MCP transport shutdown with a live GUI.

The 81 related tests passed in normal and Python `-O` modes. A broader MCP
server suite initially had one stdio child import error because its working
directory was not `/src`; with `/src` set as the container working directory,
all 29 tests passed. The first failure and corrected run are both retained.
Source hashes, conditions, outputs, target events and receipts are in the
manifest and `raw.zip`. The conditions' `draft_head` is an earlier ancestor,
while the manifest identifies the actual candidate. One test cookie was
scanned in raw and hexadecimal form against packaged files; authority files and
private commands are excluded. WSLc reported no swap-limit enforcement.

Executor `shutdown(wait=True)` is existing behavior and remains potentially
unbounded if a cancellation thread never returns. This change does not prove
a hard shutdown deadline, old task success, queue drainage, or production
private-display integration. A close that stays busy after the one retry is
reported busy; direct callers outside this helper still need to retry.
