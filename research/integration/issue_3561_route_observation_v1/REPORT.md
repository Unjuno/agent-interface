# Issue #3561 — OrbStack route equivalence revalidation

## H/T/D/C/U result

**H** — Current-main public API, CLI and stdio MCP can each make one read-only
observation of the same fixture/region and return pixel-identical images.

**T** — Source main `b092d73893ccb283def5886cdd2ee2b6c3a01089`; experiment
source `f5bb567cc902a5cb3730e8d985bf64ac5a81507e`; OrbStack Linux/arm64 image
`issue-3561-route-unit:20260920`, immutable ID
`sha256:c9660ab9c4c50c49e59e4b11ed2e642169b42d369a0a2c28eb4f77b752d91481`.
Python 3.12.3, MCP 1.30.0, Pillow 10.2.0, python-xlib 0.33. Runtime
container was `--network none`, read-only root and read-only `/repo`; evidence
was written to a separate mount. One fixed xmessage fixture was freshly
recreated for each route; target `fixture`, frame `window_client`, requested
region `[0,0,500,260]`. No model or input action. Exact raw evidence is in
`evidence/20260920-issue3561-route-unit-01/`; frozen-source independent audit
sidecar is adjacent.

**D** — `PASS_UNIT_ROUTE_EQUIVALENCE`, independent audit 36/36. Exactly one
observation per route returned `status=returned`, `image_status=image`,
`side_effect_authority=false`, `input_dispatched=false`, with matched request,
capture and cleanup. PNG SHA-256 for all three:
`c7d6ceedb02407b9a572a2334868e2a34aa2c1676845b9954d5f1a31fa9ad6d1`;
RGB pixel SHA-256:
`8403ba12891a93904dd5015f80c8a11d98af41f86cd427906eea381be690b536`.
API/CLI/MCP observed intervals were 61.028, 86.647 and 353.424 ms; these are
single samples with different timing boundaries and imply no route winner.

**C** — Compared with #3557, this is a new source commit, container image,
fixture allocation and raw output path. The retained runner uses the same
500x260 fixture/region as #3557, not the 320x240 region stated in #3561's
proposal. Therefore this result revalidates the exact earlier capture contract
on current main, but does **not** answer #3561's proposed 320x240 geometry.
The accidental preflight attempt 01 exited before any route call because the
probe queried a nonexistent `mcp.__version__`; corrected no-call preflight 02
passed. The one formal allocation completed without retry.

**U** — The actual 320x240 request remains untested. Keep #3561 open and run a
newly frozen runner parameterized to 320x240 as a distinct allocation before
closing it. Neither allocation measures model/task outcomes, token/cost,
recovery, or routing benefit.
