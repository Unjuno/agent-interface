# Allocation 03 — public MCP stale refusal and Chromium effect (Issue #2907)

Allocation ID: `public-mcp-dispatch-stale-effect-2907-docker-20260927-03`  
Branch: `research/public-mcp-stale-effect-2907-allocation03-20260927`  
Evidence path: `research/integration/public_mcp_stale_effect_2907_allocation03_v1/`  
Parent issue: open #2907; integration gate: open #2789  
Main base: `43ef66afa8ccc2823d8729093e198e0bf4eef40f`  
Preformal state: all source/test files committed and byte-exact readback verified; formal MCP calls = 0.  
Execution: local Docker Desktop only; no Actions/workflow.

## Reason for fresh allocation

Allocation 01 is preserved as STOP for caller handling of flat `interface_close`. Allocation 02's local raw result showed scoped behavior, but was not accepted as a formal result: the GitHub branch source did not match the runner SHA written into its freeze, and its first independent auditor held on an overstrict echoed-session-ID projection. Both prior outcomes and artifacts remain untouched. Issue #2789 routes source publication/auditor corrections to the same research question; this is a new allocation/path under #2907, not a new Issue. No result is pooled across allocations.

## H/T/D/C/U

- **H:** One fresh public stdio persistent-X11 MCP session rejects a stale observation-bound program before backend input, completes one fresh program with verified release and an independent exact Chromium local-page effect, closes the same session, and returns six finished/no-op retained-result reads bound to the original calls.
- **T:** One fresh Linux/amd64 container, private Xvfb/Openbox, one owner-bound Chromium window, and one local HTML page whose unique title marker is `agent-mcp-effect-2907-20260927-03`. In one stdio MCP ClientSession: observe sequence 1 and 2; dispatch an otherwise valid F6 program sourced from sequence 1 with current sequence 2; only on exact refusal `STALE_OBSERVATION`/zero backend emissions dispatch the sequence-2 fixed Ctrl+L/local-file/Enter/release_all program; persist independent `xprop WM_NAME` marker/window evidence before post-effect observation; observe; close; retrieve all six calls via `interface_results`. Fresh output is `formal03/`; one formal invocation, no retry, model/provider/network, or out-of-MCP GUI input. Independent auditor runs once in separate networkless read-only Docker with output `audit03/`.
- **D:** `PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED` requires stale refusal and 0 backend emissions; fresh dispatch completed with positive program emissions and all releases verified with no keys/buttons down; persistent exact marker/title/window-ID match; one session across six top-level calls; close closed/release attempted; six retained responses each finish, invoke no operation, match its source call ID, and are bound by the single stdio ClientSession context; clean owned process and X socket shutdown; independent raw audit has no errors and rejects all seven corruption controls. Any contrary behavior is a retained FAIL; execution/provenance/evidence interruption is STOP/HOLD. No retry or relabel.
- **C:** Base image `sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3`; derived local image `public-mcp-three-app-2907:formal01`, ID `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`, Linux/amd64. Runtime source closure is the 94-file closure SHA-256 `cf93b6cbefcd9fda5e02c82335cd9189e3ac31f303ed1b38253bcac1258a1b5d`, reconstructed from `51c04e1208014406b7422c5291c97e7023ba68f4`; main base is above and the five relevant current-main blobs were verified unchanged: MCP server `82a7841b53a0618ecbf74b4ead8157a42b62112e`, MCP session `b27dbc6c19d0a2df2b77c81a140cdc16b02d2509`, X11 backend `965443ae5b0f92eab62adfb4aaa00b8963f34679`, X11 session `e973b2f3f827951634344a320cd833a80a899d9e`, core contract `87154518107e4231a6f8ec06e976d2856b375d1d`.
  
  Exact frozen source SHA-256s (all files are committed in this branch and readback byte-matched before freeze): `runner_effect_v3.py` 5fc2d42d3dde3b7c1b6a670ef9b514da312308e3c8efe911502670c18105878f; parent `runner_effect_v2.py` `a9002d83f829dd7821d99d19598784f17bff44798ced8dcbaec9708975656507`; `runner_effect.py` `be6b29bc7d70cc1554d61615f2aeee6a3a5e715d6f10d92bc5206da654452497`; helper `runner.py` `47668fdd02600c1e13c7f43387f05b5ef3c71490be9b6f41e37ea8a986b08d75`; `auditor_effect_v3.py` `29cfffd4cbfe7ecc063b04581d7fc6785b070514c5b4b032ff638cf0a558de81`; parents `auditor_effect_v2.py` `86f24dd26cfc6036ce0487526429b3e8a048f3ec297923a4a4a92287fa376882` and `auditor_effect.py` `acb869e50202a2108d0e9742f5a4153fbcee5793a17a290e2fe615b577de04a`; construction tests `test_auditor_v3.py` `803084de29a908d301c7af50b3902d9bbea3c72967101403874d7fb400b2f93d` and `test_effect_runner_v3.py` `971688db6181eefb31b08b94d3fe5725b135edf3cfa044e787FDBE5A13905408`. Construction tests passed 4/4 in Docker before this freeze; no MCP, X server, or GUI input was used.
- **U:** One scripted local Chromium title-navigation effect and one stale-sequence negative only. Fixture lease/sequence are caller-supplied; production lease issuance/controller, model behavior, Calc/Inkscape, full #2907 focus/modal/geometry/window-replacement/return schedule, six-task #2789 acceptance, broad utility/performance/reliability/product readiness remain untested.

## Frozen invocations

Formal (one invocation only; source/helper read-only; only evidence output writable):

```powershell
docker run --rm --network none --pids-limit 512 --memory 4g --cpus 4 --env SOURCE_COMMIT=43ef66afa8ccc2823d8729093e198e0bf4eef40f --env EXPERIMENT_IMAGE_ID=sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09 --env OUTPUT_DIR=/evidence/formal03 --mount "type=bind,source=$source,target=/source,readonly" --mount "type=bind,source=$legacy,target=/legacy,readonly" --mount "type=bind,source=$v1,target=/v1,readonly" --mount "type=bind,source=$allocation,target=/experiment,readonly" --mount "type=bind,source=$allocation,target=/evidence" --entrypoint /bin/bash public-mcp-three-app-2907:formal01 -lc 'mkdir -p /opt/importroot && ln -s /source /opt/importroot/runtime && export PYTHONPATH=/experiment:/v1:/legacy:/opt/importroot PYTHONPYCACHEPREFIX=/tmp/pycache && python3 -B /experiment/runner_effect_v3.py'
```

Independent audit is a fresh separate `docker run --network none --read-only` against `/formal03`, with experiment/source/helper mounts read-only and only `audit03/` writable; invoke `auditor_effect_v3.py --bundle /formal03 --output /audit-output/audit03`. No MCP calls or input are permitted in the audit container.

Do not change frozen files, image, gates, or paths. Preserve the complete first outputs and exit status. Allocation 03 is never resumed or retried. Even a scoped PASS does not close #2907 or #2789.
