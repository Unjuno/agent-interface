# Issue #3370 — matched delivery-path pair

## H / T / D / C / U

**H.** Direct host-image and saved-file/view-image delivery can each support
one source-bound action and an independently scored Inkscape effect on a matched
task/document.

**T.** Main frozen at `bec31389157ae5237bcc6474dfd9bf9b16d30752`; OrbStack
`linux/arm64` image
`sha256:cf02676f620c6679614a311c4baee4deceb135a37cae9d6e14c39a5e8e49001e`;
seed `991123`; `--network none`; read-only root and source; private Xvfb. Two
fresh allocations used the exact same initial MCP PNG (SHA-256
`505c17b695d2c4a71b8ae5b0e52a1c90261d25764ca4d3ae9b19b2933e1abec9`) and
identical model-authored decision/action recipe. Only the presentation path
differed: direct data-image item vs saved PNG through `tools.view_image`.

**D.** `PASS_BOTH_DELIVERY_PATHS_TASK_SCOPED`. Both conditions submitted once,
with zero resume, one native action, verified empty release and cleanup, and
container exit code 0. Independent saved-SVG scores passed identically:
x=86 (>50.5), y=50, width=40, height=30, transform=null. The independent pair
audit reports zero failures.

**C.** The matching image SHA and identical decision hash establish a narrow
task/document and authored-action match. Each condition used a fresh independent
process and the same model, runtime image, source, seed, goal, and input policy.
Every raw SDK response, image, request, reply, saved file, release and cleanup
record is retained below `evidence/`; `evidence/manifest.json` hashes the full
tree.

**U.** This pair does not expose host presentation acknowledgement or model
receipt/interpretation timestamps, actual provider token/cost usage, or a
latency comparison. It is n=1 per route, with fixed route order, and does not
cover stale/delayed/no-image/disconnect controls. It neither establishes
efficiency nor completes Issue #3370; keep the issue open.

## Trial ledger

| Route | Initial image | Independent effect | Release/cleanup | Result |
|---|---|---|---|---|
| Direct MCP image item | Exact MCP PNG SHA `505c17b6…` | x=86, y=50, 40×30, no transform | Empty release verified; tracked cleanup complete; process/container exit 0 | PASS, scoped |
| Saved file then view image | Same exact MCP PNG SHA `505c17b6…` | x=86, y=50, 40×30, no transform | Empty release verified; tracked cleanup complete; process/container exit 0 | PASS, scoped |

## Revalidation

From the repository root, use the pinned OrbStack image and pass the committed
evidence directory to the independent auditor:

```sh
docker --context orbstack run --rm --network none --read-only \
  --mount type=bind,src="$PWD",dst=/workspace,readonly \
  --mount type=bind,src="$PWD/research/integration/issue_3370_delivery_comparison_v1/evidence",dst=/evidence \
  --entrypoint /opt/mcp/bin/python issue-3370-native-mcp-orbstack:20260920-r2 \
  /workspace/research/integration/issue_3370_delivery_comparison_v1/audit.py \
  /evidence
```
