# Issue #2907 — public MCP three-app successor evidence

## Disposition

Allocation 01 remains immutable: one Inkscape observation was returned, but the frozen caller expected a top-level status instead of the public nested receipt. Its original runner label `FAIL_PUBLIC_MCP_THREE_APP` is preserved. The independent stop audit classifies it as `STOP_CALLER_RECEIPT_SHAPE_NOT_INTEGRATION_FAIL`; it is not a three-app integration result.

Allocation 02 is a distinct fresh Docker container and MCP session, preregistered in `FREEZE_V2.md`. It completed the fixed Inkscape → Calc → Chromium observe sequence, explicit neutral close, and four retained reads:

- Formal decision: `PASS_PUBLIC_MCP_THREE_APP_OBSERVE_CLOSE_SCOPED`
- Session: `dccc03c1ac544b61a930a13a46c0d880`, final state closed
- Three distinct owner-bound windows: Inkscape 4194311 (710×659); Calc 10486565 (1600×981); Chromium 6291459 (1050×980)
- Observation count 3; retained-read count 4
- Input operations 0; model calls 0; network calls 0; authority granted false
- Close: `release_attempted=false`; connection close attempted; restart false
- No live owned PID, MCP server PID, or X socket remained. App processes were zombies at final collection, with no live owned processes.
- Formal result SHA-256: `950060a54ef25a7cfc26927f5d93cf19a30837f3205e5904924f823a8fb5d7d2`

An independent, separate Docker container ran offline and read-only against the formal bundle:

- Audit: `PASS_RAW_AUDIT`, errors=[]
- Corruption controls: divergent session, nonzero input, missing report, corrupt image payload — rejected 4/4
- Audit JSON SHA-256: `7c141ccf92bf6de82e13b13ce5179a55d7e9bec4a59b407040cc448aeeca90d0`

## Local execution

Docker Desktop, Linux/amd64, image `public-mcp-three-app-2907:formal01`, ID `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`; base image ID `sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3`. Formal runner used `--network none --pids-limit 512 --memory 4g --cpus 4`, the frozen runtime source read-only, and only `formal02/` writable. The separately executed audit used `--network none --read-only`, raw bundle read-only, and a dedicated audit output mount.

Formal command (one invocation; no retry):

```sh
docker run --rm --network none --pids-limit 512 --memory 4g --cpus 4 \
  --env SOURCE_COMMIT=c193b77ddf84bb77fbaa480307c4b23600feedb1 \
  --env EXPERIMENT_IMAGE_ID=sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09 \
  --env OUTPUT_DIR=/evidence/formal02 \
  --mount type=bind,source=<frozen-source>,target=/source,readonly \
  --mount type=bind,source=<allocation-evidence>,target=/evidence \
  --entrypoint /bin/bash public-mcp-three-app-2907:formal01 -lc \
  'mkdir -p /opt/importroot && ln -s /source /opt/importroot/runtime && export PYTHONPATH=/evidence:/opt/importroot PYTHONPYCACHEPREFIX=/tmp/pycache && python3 -B /evidence/runner_v2.py'
```

The MCP response transport used the public GitHub-main runtime source closure pinned in the freeze. Five relevant main-file blob IDs matched the previously frozen source. The sole successor treatment was an additive caller/auditor projection of the public nested receipt schema; inherited v1 runner and auditor source bytes were not modified. Schema tests passed 3/3 inside a no-network Docker container before preregistration. Construction/setup errors and earlier preflight history are preserved in the frozen records and are not formal rows.

## H/T/D/C/U and integration boundary

See `FREEZE_V2.md` for the complete pre-call H/T/D/C/U and exact gates. This PASS is limited to public-MCP persistent-session setup, three owner-bound observations, neutral close, retained reads, and raw-evidence audit. It does not establish guarded input, app effects, the full #2907 controller hypothesis, #2789 six-task acceptance, task success, model integration, efficiency, broad reliability, production readiness, or roadmap completion. No runtime source was changed. Preserve #01 and all historical Issue results unchanged.

## Evidence map

- `FREEZE.md`, `FREEZE_V2.md`: allocations 01 and 02; hashes and gates
- `formal01/`, `audit-stop01/`: original STOP and both original audits
- `formal02/`, `audit02/`: complete successor raw result, MCP calls, server receipts/images, and independent audit
- PNG bytes are losslessly retained as adjacent `.png.b64` text files so the GitHub text-file interface cannot alter binary data; `EVIDENCE_MANIFEST.json` records original paths, encoded paths, byte counts, and SHA-256 for every published file.
- `runner.py`, `auditor.py`, `runner_v2.py`, `auditor_v2.py`, `preflight.py`, `stop_auditor.py`, `stop_auditor_v2.py`, `test_receipt_projection.py`: reproducibility and retained predecessor audit tools
- `Dockerfile`, `requirements-lock.txt`: image build inputs

GitHub Actions/workflows were not used or dispatched. Research was performed locally in Docker Desktop; GitHub MCP was used to inspect and retain the preregistration/evidence.
