# #3711 report write/fsync residue protocol v1

Status: preregistered before test edits; no execution result claimed.

## H / T / D / C / U

**H — hypothesis.** `_write_json` writes to `.report.json.tmp`, flushes and fsyncs it, then atomically replaces `report.json`. A partial write or fsync failure after request publication may leave a temp file with no final report. The read-only `attempt-status` should classify the attempt as `unknown_or_incomplete`, list the residue, never authorize replay, and leave the file bytes untouched. A successful write should leave no temp files.

**T — target.** Fresh additive branch `research/cli-fault-residue-3711-v1`; freeze current-main blob `runtime/cli_v1/attempt.py` SHA `70cc62b450c8b9c8aaa0db49b1e116388368fe4c` and `runtime/cli_v1/test_attempt.py` SHA `0aebdb6e3033a1a05ea56b2847194a0ef3b225de`. Add deterministic fault-injection tests for (1) a partial write then OSError on report temp, and (2) the second fsync (request fsync succeeds; report fsync fails). Also assert successful report publication leaves no temp residue. Each failed case must invoke the synthetic backend exactly once, leave final report absent, surface `.report.json.tmp` in `attempt-status`, return `unknown_or_incomplete`/replay=false, and preserve residue bytes across repeated read-only inspections. Preserve `#3725`'s rename-failure result unchanged. No GUI/model/input/network.

**D — decision.** Scoped PASS only if all three frozen tests pass in the Runtime CLI workflow on Linux, Windows, and macOS; both injected failures satisfy every status/call-count/residue invariant; success leaves no temps. FAIL for hidden residue, incorrect success/replay classification, changed/deleted residue, extra backend invocation, or wrong temp lifecycle. HOLD for any queued/incomplete platform. CI infrastructure failure is STOP, not test FAIL/PASS. No result until workflow completes.

**C — constraints.** Local C: is currently 0 bytes free and Docker Desktop's Linux engine pipe is unavailable. Do not run local tests, start/repair Docker, pull images, or delete/prune files. Existing CI is remote platform validation and is not a local Docker pass. This tests process-level write/fsync errors, not hardware power loss or every filesystem durability mode.

**U — limits.** Finite injected report-write/fsync points and one success path only. It does not prove crash/power-loss durability, cleanup of arbitrary temp names, all filesystem semantics, or full #3711 adoption. Keep the parent issue open for other gates.
