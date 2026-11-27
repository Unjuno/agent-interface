# Real stdio cancellation with Fake X

Base main 155dc4f69c0c5aeda36788d652823ca2efc5d8fb. H: the standard
MCP stdio server can receive a second cancellation request while guarded input
is pending; active visual isolation lets the input result return before a
blocked capture resumes. Direct server.call_tool tests do not establish this
cross-process transport property. Existing stdio tests use a FakeBridge instead.

T: freeze six cells per normal/optimized Python: target-query-only and active
visual isolation, each healthy / blocked capture with cancel / blocked capture
with original expiry. Each cell launches one child via mcp.client.stdio and runs
the actual runtime.cli_v1.mcp_server.main with explicit policy flags. The child
installs Fake X transport and a trusted local visual-input guard, then delegates
to real NativeHandleBridge keyboard/public dispatch/session/backend cleanup.
No tool is added or replaced. The input guard is bootstrap configuration, not
a remotely supplied callable or a default MCP feature. Platforms/preflight/focus
and target-query replies remain fake. Real JSON-RPC framing, stdio, child startup,
tool discovery/selection, worker admission, result lookup and close are exercised.

D: healthy arms must emit CTRL+a and return verified fake-neutral cleanup.
At the capture gate, both fault arms must hold CTRL. Cancel uses only the ID
discovered by interface_results; wrong ID is ignored and acknowledgment never
claims release. Expiry instead advances the child fake clock to the original
five-second deadline. With the gate still closed, target-query-only must remain
pending/held; isolated must return failed execution with verified fake release
and no following a press. After release of the gate, neither arm may publish a
late task press. Retained lookup must equal the original result and emit nothing;
explicit interface_close must complete. Otherwise preserve FAIL/inconclusive.

C/U: gate files and emission snapshots are harness instrumentation, not native
physical observation. A 10-second gate guard and 3-second parent watchdog are
harness caps, not release guarantees or latency confidence bounds. Parent
perf_counter brackets measure client receipt only; child fake monotonic clock
is separate. No model/application/GUI/container/WSL allocation, task success or
efficiency claim. All child stderr and actual bridge artifacts are retained.
First outputs refuse overwrite. Always release gates in finally; preserve
partial output if setup or collection fails. Retain frozen source/dependencies,
raw summaries, artifact hashes and a saved-data-only mutation audit.
