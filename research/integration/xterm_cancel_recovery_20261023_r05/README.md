# Real xterm cancellation and new-generation recovery — R05

## Frozen question

Does R04’s scoped result repeat in a fresh native WSL2 trial: a public guarded MCP input blocked at the real delayed-XTEST / `Display.sync()` boundary, bounded cancellation with verified supervisor key-up but conservative old-task `UNKNOWN`, then one independently saved task on a new xterm generation after the finite late-request horizon?

This is an independent run with new run ID `xterm-cancel-recovery-local-20261023-r05`, display `:191`, old task `old05`, new task `new06`, and separately retained journals. It uses the same rootless Xvfb/xterm binaries and Python environment previously recorded in R04, with fresh byte hashes in this packet. A new input-free xterm/PTY preflight on private display `:192` passed and is bound by byte digest in `conditions.json`; it issued no public input and produced no task effect. No live task is repeated from R04.

## Decision rule

`audit_reconciled.py` is frozen and source-bound before the live input run. It requires one old pending public input request, a real queued delayed request and `Display.sync()` wait, cancellation within 3,000 ms, independently verified all-up readback while the caller remains `UNKNOWN` with replay disallowed, no more than one observed old effect without changing that unknown result, a full 9,000 ms horizon before fresh focus, exact old session retirement, distinct process/window generation IDs, one new `new06` PTY effect with fsync receipt, and clean session/Xvfb shutdown. Numeric native XID may be reused or differ; generation identity must change.

A pass is one additional sample only. It will not establish broad reliability, MAP01, real provider/model economics, or matched efficiency. Failure outcomes and partial artifacts remain immutable; do not retry this live run.

## R05 observed outcome

The new no-input preflight passed on private display `:192`: a real `XTerm` window with an interactive `/dev/pts` shell, zero public input calls, zero task effects, zero held keys, xterm exit 15, Xvfb exit 0, and no process/session or display-socket residue. Its report is fixed by SHA256 in `conditions.json`.

The one formal R05 run passed all 16 reconciled checks. Cancellation returned in 97.198 ms. The prestarted supervisor read all keys and buttons up, while the old public attempt remained `UNKNOWN`, task success unset, release confirmation false, and replay disallowed. No old journal row was observed at cancellation or after the full 9,000 ms horizon; the task result remains unknown. The old xterm session exited before the new target was focused. XID `4194316` was reused, with different process and window generation IDs. The new task produced one `new06` PTY journal row and fsync receipt. Public input returned 86.329 ms after invocation; fsync committed 106.570 ms after invocation, 20.241 ms after public return. Xvfb exited 0 and its lock/socket were absent afterward; `cleanup-readback.json` records a post-run process scan and both private displays had no remaining socket or lock.

`matched_repeat_comparison.json` records R04 and R05 side by side. Both scoped samples passed with one new saved effect and an old task held UNKNOWN. Their cancel responses were 97.416 ms and 97.198 ms; their fsync receipts followed public input returns by 21.168 ms and 20.241 ms. Two samples show repeatability under this exact injected xterm condition, not a reliability rate or a result for MAP01, provider/model economics, or other applications.

The two source files produced through PowerShell retain their exact pre-run bytes, including the final blank line covered by `SOURCES.json`. The matching packet-specific whitespace attributes preserve those frozen bytes in Git and keep whitespace checks clean.
