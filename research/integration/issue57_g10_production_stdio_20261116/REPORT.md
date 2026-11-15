# G10 public CLI/stdio receipt join — 2026-11-16

## Result

Added `runtime.cli_v1.test_mcp_g10_production_stdio`, which starts the real
`mcp_server.main()` CLI in a subprocess and uses an MCP stdio client to call the
registered G10 workflow. A Fake X owner and archived FODS snapshots supply the
synthetic target/effect. The test crosses public prepare, launch/review, alias
minting, compiled execution, exact result lookup, close, and parent effect
verification. A pending launch is polled by its exact call ID until the terminal
`candidate_found` receipt arrives. Both saved-action receipts retain release
verification; after close, the parent verifier returns `verified` and
`task_success=true` for the two retained formula files.

CPython 3.11.9 on Windows: 1/1 normal (14.013 s) and 1/1 under `-O`
(14.377 s). Raw runner captures are under `raw/`.

## Main rerun (2026-11-16)

After PR #10327 merged as `156fd8fad2c94e8ece74e2f6ae4885f9cd998636`,
the same committed test was rerun from that main commit. Both normal and
`-O` passed 1/1 (15.107 s and 15.359 s). The instrumented owner startup
measurements were 10.890 s and 11.578 s. Full raw captures are
`raw/rerun-normal.log` and `raw/rerun-optimized.log`, included in the manifest.
This independently reproduces the stdio receipt join and also confirms that
the nested Windows-spawn `get()` duration is 10.890 s / 11.578 s. These are
end-to-end `get()` timings, not direct measurements of the production readiness
wait.

## Startup boundary

The first nested Windows stdio/owned-process attempt used the production 5 s
owner startup budget and returned `CALC_LAUNCH_OR_DISCOVERY_FAILED` with
`owned guarded process startup timed out`; parent custody remained UNKNOWN,
authority was not granted, and no target launch or input was reported. The
structured result appeared in the test runner output but was not separately
captured as a raw file; the failed outcome is preserved in `ATTEMPT_NOTES.md`.

For the stdio receipt-shape test only, the test server changes its fixture
startup wait to 20 s. It does not modify the production constant. Instrumented
`OwnedGuardedSessionOwner.get()` took 10.860 s normally and 11.031 s under
`-O` (two observations; median 10.946 s). The production `_STARTUP_TIMEOUT_S`
is applied by `rpc_parent.poll()` **after** `process.start()` returns; that
constant does not bound total `get()` wall time. The timed wrapper measures the
whole `get()` and does not split process-start time from the readiness poll.
The initial default-budget attempt establishes only that no readiness message
arrived within the 5 s poll after `process.start()` returned. Thus the positive
run validates transport and receipt joining under the test-only 20 s readiness
wait, while the exact source of the default readiness timeout is unresolved.
Linux X11 and process-start timing were not measured; no conclusion about Linux
deployment follows.

## Limits

This is Fake X and archived-artifact evidence. It does not establish live Calc,
MAP01 task effect, native Win32 recovery, WSLc allocation, provider usage, or
Issue #57's matched lifecycle/economic comparison. No Docker, WSLc, or live
input operation was performed.
