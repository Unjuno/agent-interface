# Issue #3544 first unit result — MCP, API and CLI observation routes

Successor allocation: #3557. Predecessor #3548 attempt 01 remains
`STOP_BEFORE_ROUTE_CALL` in `ATTEMPT_01_STOP.md`; no predecessor route was run.

## H/T/D/C/U

**H** — On one pinned OrbStack Linux/arm64 fixture host, direct public Python
API, CLI and stdio MCP can each invoke the same read-only observation contract
and return equivalent image evidence.

**T** — Exact main source `987d792b4b5d5075335d75036b924c190a411fa9`; frozen
experiment runner/auditor commit `e79696bf7194b1730eaa0c1d1c53baaf5ea07dda`.
The container used image
`issue-3548-route-unit:20260920` / immutable ID
`sha256:0e35cdb51a82e59d359ec09b85ce835d9217a1eab65b68ce1871c9b0a85014c9`,
OrbStack context, Linux/arm64, Python 3.12, MCP SDK 1.30.0, isolated Xvfb,
`--network none`, read-only `/repo`, and a writable append-only evidence mount.
For each route, the same fixed xmessage fixture was freshly launched and
terminated. Exactly one call used target `fixture`, frame `window_client`,
region `[0,0,500,260]`; no task, model call or input was involved. Raw evidence
and hashes are under
`evidence/20260920-orbstack-route-unit-02/` and its sibling independent audit
report.

**D** — `PASS_UNIT_ROUTE_EQUIVALENCE`. The independent auditor reports 36/36
checks true. All three routes returned status `returned`, `image_status=image`,
500x260 image, matching raw-capture lineage, target/frame/region, and identical
PNG SHA-256 `c7d6ceedb02407b9a572a2334868e2a34aa2c1676845b9954d5f1a31fa9ad6d1`
and RGB pixel SHA-256
`8403ba12891a93904dd5015f80c8a11d98af41f86cd427906eea381be690b536`.
Every route records `side_effect_authority=false` and
`input_dispatched=false`; all fixture processes were reaped. CLI exited 0. MCP
listed `interface_observe`, returned its image as a distinct PNG block, and its
identified child process was reaped when stdio closed. Raw manifest, frozen
source hashes, image ID, runtime isolation and MCP version all audit true.

Observed call-boundary intervals were API 47.514 ms, CLI subprocess 82.431 ms,
and MCP 357.250 ms. These are one ordered sample, not a causal comparison: API
includes API+common image review, CLI includes subprocess startup, and MCP
includes server startup, initialization, tool discovery, call and shutdown.
They establish no latency benefit or routing preference. Model tokens/cost are
unknown because no model was invoked.

**C** — The host-local public MCP server was actually started as a stdio child
inside OrbStack; this demonstrates that the repository's MCP route can be
launched in this controlled host, not that every external agent host has it
configured. The X server reused native XID 4194321 after each fixture process
was terminated; no observation or action was reused. One fixture recipe and
identical pixels were independently verified. No model, network, GUI input or
task action occurred. Attempt 01's STOP remains unchanged.

**U** — This unit shows transport availability/equivalent read-only pixels only.
It does not show equivalent model-visible tool definitions, token/image usage,
task correctness, recovery behavior, costs, or a routing policy. The next
research step is a separate preregistered matched model/task comparison charging
all route definitions, actual text and image inputs, errors/recovery, and
router overhead. A one-task sample must be treated as that single attempt, not a
general performance claim.
