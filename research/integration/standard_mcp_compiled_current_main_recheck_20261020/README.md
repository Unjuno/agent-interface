# Current-main standard compiled MCP caller recheck

This Windows-local construction check used the complete `origin/main` tree at
`577ddc30c918c422ddebab8a12eb133649fc789a` and Python 3.11.9. Five focused
public-caller tests passed 5/5 in normal mode and 5/5 under `-O`; complete output
is retained in [`raw/`](raw/) and exact conditions/source hashes are in
[`conditions.json`](conditions.json).

The selection covers: endpoint absence without an owned process; invalid
profile refusal before call admission; successful invocation of the public
`interface_guarded_compiled` tool through the generation-bound owned caller;
mid-method refusal when process generation changes; and cancellation while
Fake X input synchronization is blocked. The cancellation case retires the
owned process and preserves obligations, but the fixture returns release
`UNKNOWN`, keeps replay denied, and leaves `task_success` null.

This confirms that current main has a public compiled-MCP composition path;
older plan text describing the Python owner as the only path is stale. The
profile is fixed, declarative exact-pixel logic with no model/provider caller or
independent application scorer. Fake X construction does not establish live
physical release, release under a stopped X server, MAP01 success, bounded
recovery, end-to-end observation/effect timing, or matched efficiency. No live
GUI, Xvfb, WSLc or allocation was used.
