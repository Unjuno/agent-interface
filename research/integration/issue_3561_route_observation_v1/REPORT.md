# Issue #3561 — OrbStack route equivalence revalidation

## H/T/D/C/U result

**H** — Current-main public API, CLI and stdio MCP can each make one read-only
observation of the same fixture/region and return pixel-identical images.

**T** — Source main `b092d73893ccb283def5886cdd2ee2b6c3a01089`; the valid
320x240 allocation froze experiment source
`bdef682a98bc0df2fe61d42ee23aa57ab3f53da9`; OrbStack Linux/arm64 image
`issue-3561-route-unit:20260920-v2`, immutable ID
`sha256:ead0ccaee722c8fa1984b85f1a16d12202085439f750a45070df02a17f0b26b6`.
Python 3.12.3, MCP 1.30.0, Pillow 10.2.0, python-xlib 0.33. Runtime
container was `--network none`, read-only root and read-only `/repo`; evidence
was written to a separate mount. One fixed xmessage fixture was freshly
recreated for each route; target `fixture`, frame `window_client`, requested
region `[0,0,320,240]`. No model or input action. Exact raw evidence is in
`evidence/20260920-issue3561-route-unit-02/`; frozen-source independent audit
sidecar is adjacent. Allocation 01 is separately retained and audited, but it
used 500x260 and is not counted as a test of the issue's 320x240 condition.

**D** — `PASS_UNIT_ROUTE_EQUIVALENCE`, independent audit 36/36 on allocation
02. Exactly one
observation per route returned `status=returned`, `image_status=image`,
`side_effect_authority=false`, `input_dispatched=false`, with matched request,
capture and cleanup. PNG SHA-256 for all three:
`ee99e3da9f9baeaf6032e5b99d9286f6d4fdcab358952457e4c17e0c0b475309`;
RGB pixel SHA-256:
`959dbbf434daa78c7e2c6bb18ea46d16f010d2f52d585eb23f789386a40e26ef`.
API/CLI/MCP observed intervals were 55.779, 82.967 and 352.895 ms; these are
single samples with different timing boundaries and imply no route winner.

**C** — Compared with #3557, this is a new source commit, container image,
fixture allocation and raw output path. A first formal candidate allocation
used 500x260 due to a runner default; it is retained as allocation 01 and is
not substituted for the issue's target condition. Allocation 02 set and audited
320x240 explicitly and passed. Preflight attempt 01 exited before route calls
because the probe queried nonexistent `mcp.__version__`; corrected no-call
preflight 02 and 03 passed. No failed route call was retried.

**U** — The unit-level 320x240 route-equivalence question is answered for this
one OrbStack fixture allocation. #3561 may close as a bounded observation-unit
issue after PR integration, but the parent #3544 remains open: neither
allocation measures model/task outcomes, token/cost, recovery, or routing
benefit. Continue with a separately preregistered matched agent/task study.
