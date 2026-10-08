# Issue #3370 — stale source identity control

## H / T / D / C / U

**H.** A real managed MCP/Inkscape input request bound to a superseded source
sequence is rejected before action publication, with no native input and a
cleanly closed allocation.

**T.** Main frozen at `21425ed43b55d7eeb1b608d2e127c9fab7f6acc8`; OrbStack
`linux/arm64` image `sha256:cf02676f620c6679614a311c4baee4deceb135a37cae9d6e14c39a5e8e49001e`;
network disabled, read-only root/source, private Xvfb, one fresh Inkscape task,
seed 991123. Exact commands, source hashes and retained MCP exchanges are
recorded alongside the evidence.

**D.** `PASS_STALE_SOURCE_REFUSED_ZERO_INPUT` (one fresh allocation). MCP
source 1 was observed, a read-only stage-1 observation returned source 2, then
one stage-2 click bound to source 1 was rejected with
`decision must name the presented source`. The stale action request was not
published. Stage 2 was subsequently completed only by a current-source
read-only observation; stage 3 used an explicit no-input finish. `actions.json`
is absent; the owner reached terminal return code 0; cleanup report is
`completed` with tracked processes terminal. The sealed v3 auditor ran inside
the pinned OrbStack image and reported zero failures. Related MCP, finish-after,
runtime-contract and X11 text-plan tests passed 48/48 in the same container.
Evidence manifest: 159 files, SHA-256
`3d60f4a508da3223101aa78c56fc574b4d073c4455ea065ae201133155ead02e`.

**C.** This is a real MCP client/server interaction with a fresh live GUI owner,
not a helper-only fixture. The stale request passed schema validation but failed
the exact source-sequence check. Same seed yielded identical PNG bytes at
sequence 1 and 2; freshness was established by the new capture/source identity,
not by pixel difference. No stale request was retried. The sealed trial used
v3 preregistration/freeze after finding a stale digest in the earlier v2 freeze;
the v2 outcome is retained but excluded from the formal pass count.

**U.** n=1; proves only fail-closed stale source-sequence rejection on this
managed Inkscape route. Does not test missing/delayed image delivery,
disconnect/cancellation, contradictory task postcondition, presentation
acknowledgement, model receipt time, latency, tokens/cost or task success.
Issue #3370 remains open.

## Preserved non-pass attempts

- `PREFLIGHT_STOP.md` / `evidence/stale_source/`: real allocation reached source
  2 but the first client misread a compact receipt and stopped before stale
  submission; owner cleanup was incomplete.
- `DEVELOPMENT_PROBE.md` / `evidence/development_probe_invalid_sequence/`: an
  unregistered sequence-zero probe was rejected by MCP schema, then the client
  crashed parsing its error; cleanup was unverified. Not included in the formal
  pass count.

Neither predecessor was edited or reclassified as a pass.

The earlier `stale_source_v2` allocation also showed the intended runtime
behavior, but its frozen client/auditor digests did not match the final bytes
used. Its evidence remains intact and it is excluded. The sealed v3 allocation
is the sole formal PASS.

## Revalidation

From repository root (with the pinned image available):

```sh
docker --context orbstack run --rm --network none --read-only \
  --mount type=bind,src="$PWD",dst=/workspace,readonly \
  --mount type=bind,src="$PWD/research/integration/issue_3370_stale_source_rejection_v1/evidence",dst=/evidence \
  --workdir /workspace --entrypoint /opt/mcp/bin/python \
  issue-3370-native-mcp-orbstack:20260920-r2 \
  /workspace/research/integration/issue_3370_stale_source_rejection_v1/audit.py \
  /evidence/stale_source_v3
```
