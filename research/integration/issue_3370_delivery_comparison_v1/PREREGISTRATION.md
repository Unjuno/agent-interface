# Issue #3370 — matched direct-image / saved-file delivery pair

## H / T / D / C / U

**H.** For the same fresh managed Inkscape task and fixed action policy, both
direct MCP-image delivery and the prior saved-file/view-image route can support
the same model-authored source-bound action and independently scored saved
effect. The task quality comparison is the target; latency/efficiency is not.

**T.** Freeze current main `bec31389157ae5237bcc6474dfd9bf9b16d30752`, the
existing OrbStack `linux/arm64` image
`sha256:cf02676f620c6679614a311c4baee4deceb135a37cae9d6e14c39a5e8e49001e`,
seed `991123`, app/task, runner/auditor hashes, and the one action recipe below.
Run two fresh isolated containers sequentially, one per delivery condition:
`direct_mcp_image` forwards the exact MCP PNG bytes as an image item;
`saved_file_view_image` saves the same returned MCP PNG and presents that file
through the existing image-viewer path. Both runs use one persistent MCP stdio
session, one initial source, one authored decision, one submit with
`finish_after`, no replay, `--network none`, private Xvfb, read-only source/root,
and dedicated evidence mounts.

Action recipe, fixed before either launch: click observed rectangle at
`[600,389]`, wait 50 ms, send 18 explicit `Right` key chords, wait 50 ms, send
`CTRL+S`, wait 300 ms, and finish. Both allocations use the same deterministic
Inkscape seed so their initial task/document and public scoring goal are
matched. They are independent fresh processes and outputs.

**D.** A condition passes its task gate only if the exact returned MCP image
hash is retained, the one decision refers to source sequence 1, one request is
submitted exactly once, the independent saved-SVG oracle passes
`x>50.5, y=50, width=40, height=30, transform=null`, the release record is
verified empty, cleanup is complete, and the managed process exits zero. Pair
disposition is `PASS_BOTH_DELIVERY_PATHS_TASK_SCOPED` only if both condition
gates pass and initial PNG bytes/hashes match; otherwise preserve each result
and report `FAIL`/`HOLD` without retrying a consumed allocation.

**C.** Only the pre-model presentation route differs. Same model, task seed,
runtime digest, source, runner/auditor, and action recipe. The independent audit
reads retained raw MCP blocks, immutable requests/replies, PNGs, SVGs, release,
cleanup and process exit.

**U.** Host presentation acknowledgement, model-visible receipt/interpretation
time, provider usage, tokens/cost, and latency are unavailable. Matching task
success does not establish delivery equivalence beyond these two runs or any
speed/cost benefit. No stale/delayed/no-image/disconnect controls are in this
pair; #3370 remains open pending them and its directly observed boundary.

## Frozen identifiers

- `evidence/direct_mcp_image/`
- `evidence/saved_file_view_image/`
- `evidence/audit.json`
- `evidence/manifest.json`
