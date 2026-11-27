# Standard-caller shutdown while cancellation remains pending

## Question

Does the current public MCP server finish graceful lifespan shutdown within a
finite bound if its owned-session `close()` returns while the one-worker
cancellation executor still has a pending operation?

## Result

On current main `553efc9867632c58cc881b50a7719e7847c22bf8`, r03 exercised the
actual in-process `PublicArgumentMCP.call_tool` path and its MCP lifespan on
Windows CPython 3.11.9. A repository Fake X owner entered a synthetic
`Display.sync()` block after the CTRL key-down marker. The test held the
standard caller's cancellation callback on an event. The public cancel call
returned `pending` in 313 ms and retained an operation ID. During lifespan
shutdown, the instrumented `OwnedGuardedSessionOwner.close()` returned, but
shutdown was still incomplete 500 ms later while the cancellation callback
remained held. The total time to that observation was 5,578 ms, including the
existing bounded action-worker drain. Releasing the callback let shutdown
finish.

The exact source path calls `cancellation_executor.shutdown(wait=True)` in
`close_owner()` after `owner.close()`. This run demonstrates that an outstanding
cancellation callback can keep lifespan shutdown waiting after owner close has
returned. The operation result remained conservative: the action ended as
`runtime_failed`; release was false, cleanup `UNKNOWN`, task success null, and
replay denied. The retained session snapshot still said `open` and owner
`alive=true`, while a Win32 `OpenProcess`/`GetExitCodeProcess` read for that PID
reported it exited. Treat the retained liveness as stale, not as evidence the
process survived shutdown.

## Provenance and limits

The primary retained run is [r03](r03/). It uses the repository Fake X
owned-process fixture and a test-gated cancellation callback; it does not
exercise XRes, a real X server, physical input, a provider/model, a standard
stdio client, or an application task oracle. `release_confirmed=false`,
`cleanup_status=UNKNOWN`, `task_success=null`, and replay denial remain the
only supported safety conclusions. This is one local construction run, not a
reliability estimate or a general shutdown-time guarantee.

r01 stopped before probe entry on a Python import-path error; its failure is
preserved at the packet root. r02's complete raw output is retained, but its
probe source was not separately hashed at capture and its `os.kill(pid, 0)`
liveness check was misleading on this Windows host: an immediate `Get-Process`
query found no such PID. Treat r02 as exploratory. r03 replaces that check with
the Win32 process-query API and is the primary result. The run conditions and
all retained file hashes are recorded in `conditions.json` and `SHA256SUMS`.

No WSL, WSLc, Docker, live X server, physical input, model, or provider was used.
The host inventory showed Ubuntu and Docker Desktop distributions stopped; no
WSLc allocation was verified unused or consumed.

## Reproduction

From the repository root on Windows with the local Python dependencies:

```powershell
python -B research/integration/standard_caller_shutdown_cancel_drain_20261022/probe.py
```

`r03/stdout.json`, `r03/stderr.txt`, and `r03/exit.txt` preserve the primary
run. The harness source is `probe.py`; source hashes at run are retained in
`source-hashes-at-run.txt`.

## Decision and next discriminator

This is an integration failure boundary for bounded recovery: a bounded cancel
response does not establish a bounded server shutdown, and the retained owner
snapshot does not refresh to the post-shutdown process state. Before promoting
the prestarted supervisor, test its opt-in standard-caller composition against
this exact gate: shutdown must finish within its declared budget while a
cancellation remains blocked, then retain a fresh terminal owner/session
receipt. The current draft PR explicitly leaves startup/shutdown custody open;
do not interpret this construction test as satisfying that gate.

A read-only check of the then-current PR #9315 head
`76626da8b03df25024d12efb5f1dde2f12c53ed2` found that its
`runtime/cli_v1/mcp_server.py` still calls
`cancellation_executor.shutdown(wait=True)` after `owner.close()`. This source
comparison is a review lead, not a run of that draft's opt-in supervisor path.

On the same exact main checkout, the focused owned-process and guarded MCP
regression suites passed 77/77 in normal Python and 77/77 under `-O`. Those
tests preserve the caller's existing conservative cancellation behavior; they
do not refute the separate lifespan-shutdown observation above.
