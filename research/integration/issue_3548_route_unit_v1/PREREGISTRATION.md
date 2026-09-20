# Issue #3557 — fresh route unit allocation

Parent proposal: #3544. This allocation follows and preserves #3548 attempt 01,
which stopped before any route call because the runner had not added `/repo` to
`sys.path`. The failed container is not evidence about route availability.

## H/T/D/C/U

**H** — On a single pinned Linux/arm64 OrbStack X11 fixture host, the public
Python observation API, CLI and stdio MCP can each make one read-only capture of
the same logical fixture with the same target/frame/region and identical RGB
pixels. Startup, presentation and image-block transport may differ; this unit
does not select a winner.

**T** — Source main is `987d792b4b5d5075335d75036b924c190a411fa9`. Freeze the
experiment runner/auditor hashes in the branch commit, and image identity after
build. Preflight imports and XTEST/fixture availability without route calls.
Then perform exactly one API, one CLI subprocess and one MCP stdio observation,
recreating the same 500x260 xmessage fixture each time. Use `window_client`,
region `[0,0,500,260]`; run in OrbStack with `--network none`, read-only source,
isolated Xvfb and a dedicated writable evidence mount. Retain requests, raw
reports, PNGs, separate MCP image block, route timings/process identities,
fixture cleanup, source/image/package metadata and a raw SHA-256 manifest.
Independently audit after container exit. If a route fails, preserve that one
outcome and stop; do not retry it.

**D** —
`PASS_UNIT_ROUTE_EQUIVALENCE` requires all three outputs to be returned and
read-only, exactly one route call each, capture metadata matching request
binding, correct image/raw-capture lineage, 500x260 dimensions, identical RGB
pixel hashes, verified fixture reaping and a complete matching manifest.
`STOP_ROUTE_UNAVAILABLE`, `FAIL_SEMANTIC_MISMATCH` and `HOLD_AUDIT` are retained
as distinct non-pass outcomes. Model tokens/cost are unknown; no task,
efficiency, latency-benefit or router-policy claim follows.

**C** — Fresh same-recipe fixture per route; same source, image, display, frame
and region. No model, input action, network access or stale observation reuse.
API in-process time, CLI process time and MCP startup/discovery/call/shutdown
time are reported separately as route-boundary measurements, not as a causal
performance comparison.

**U** — Does this one host expose all three usable transports with equivalent
image evidence? Only a pass enables a separate preregistered same-model task
comparison that includes tool definitions, actual text/image usage, failures,
recovery and routing overhead. Issue #3548 attempt 01 remains immutable.
