# Public persistent MCP: three-app observation and close

Allocation: `public-mcp-three-app-observe-close-2907-docker-20260927-01`  
Parent: open Issue #2907; integration convergence context: open Issue #2789  
Formal status: frozen, not yet invoked  
Execution policy: local Docker Desktop only; no GitHub Actions/workflow

## H/T/D/C/U

- **H — hypothesis:** One current-main public stdio MCP client can observe three separately identified live app windows (Inkscape, LibreOffice Calc, Chromium) through one opt-in persistent X11 owner; returned observations/reports retain one session identity, and an explicit observation-only close is neutral while retained results remain readable after close.
- **T — treatment:** One fresh `linux/amd64` container, private `Xvfb :142` and Openbox, and one each of Inkscape → Calc → Chromium. Resolve each target only from a new visible window with the expected `WM_CLASS`, nontrivial geometry, and `_NET_WM_PID` inside that launched process's ancestry. Start exactly one stdio MCP client/server with `--session-mode persistent-x11`; call `interface_observe` once per app in the fixed order, call `interface_close` once, then read all four retained results. No dispatch, keyboard/pointer input, model, external service or retry. Run the independent raw auditor once in a separate offline container after collection.
- **D — decision:** `PASS_PUBLIC_MCP_THREE_APP_OBSERVE_CLOSE_SCOPED` only if all three class/owner-bound target IDs are distinct, all observations and the close receipt bind to one session ID, all three responses contain returned PNGs and explicit no-input/no-authority flags, close reports `release_attempted=false`, connection close attempted and closed session state, all four finished results remain retrievable with `operation_invoked=false`, every owned process and the X socket stop, and the independent auditor reproduces the records and rejects all frozen corruption controls. Any missing setup/identity/transport/report/image/cleanup/audit evidence is STOP/HOLD/FAIL; no substitution or repeat.
- **C — controls:** Fixed main/source closure, image, target class/owner gate, display geometry, call order and observation region `[0,0,128,96]`. The three app rows are not pooled or replaced. Construction probes are separate from the one formal invocation.
- **U — limits:** This is the public-MCP setup/target/observation/close transport rung only. It is not guarded input, app-effect scoring, a complete #2907 controller path, #2789 six-task acceptance, model integration, latency/token benefit, human-tempo evidence, broad reliability or production support. It does not replace #2821 fixture results or prior #2907 STOP/FAIL records.

## Frozen source and environment

- Latest intake `main`: `3a67da7a3c1833871f1afc8581bce6a12141d61f`.
- Runtime source closure: 94 files reconstructed from `51c04e1208014406b7422c5291c97e7023ba68f4`. The two later commits `80d42facd258d9d545c07270e3af041542c97f87` and `3a67da7a3c1833871f1afc8581bce6a12141d61f` change only `research/**`; GitHub MCP readback blob IDs for the public server, session owner, X11 backend/session and core contract match the local 51c04 source. Canonical SHA-256 manifest digest: `cf93b6cbefcd9fda5e02c82335cd9189e3ac31f303ed1b38253bcac1258a1b5d`.
- X11-relevant Git blobs: `runtime/cli_v1/mcp_server.py` `82a7841b53a0618ecbf74b4ead8157a42b62112e`; `runtime/cli_v1/mcp_session.py` `b27dbc6c19d0a2df2b77c81a140cdc16b02d2509`; `runtime/backends/x11_v1/backend.py` `965443ae5b0f92eab62adfb4aaa00b8963f34679`; `runtime/backends/x11_v1/session.py` `e973b2f3f827951634344a320cd833a80a899d9e`; `runtime/core_v1/contract.py` `87154518107e4231a6f8ec06e976d2856b375d1d`.
- Base image: local `mixed-app-2499-xauth:v4`, repo digest `sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3`.
- Derived image: `public-mcp-three-app-2907:formal01`, image ID/repo digest `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`, Linux/amd64. Python 3.12.14, `mcp==1.30.0`, `python-xlib==0.33`, Pillow 12.3.0 and all resolved Python dependencies are pinned in `requirements-lock.txt`.
- Runtime invocation: `docker run --rm --network none --pids-limit 512 --memory 4g --cpus 4 ... public-mcp-three-app-2907:formal01 ...` with the frozen source mounted read-only and only the new allocation output mounted writable. Image construction/pip download happened before freeze; the experiment/audit containers have no network.
- Frozen local source: `runner.py` SHA-256 `47668fdd02600c1e13c7f43387f05b5ef3c71490be9b6f41e37ea8a986b08d75`; `auditor.py` `57165a818e9f36231f135051af3f2191007f9219e1ca072e26fb0bba9869efc1`; `preflight.py` `918b7ede82d86c9cd930a365160128e2b1e277abacb18e0586b9305d640e4750`; Dockerfile `2630bff415bbfb06f90742c1f1dfb48966b30d2abf0c542fb04488698c3ee89b`; dependency lock `5933e93e0dc95ee7011794f237dc05626c2b054b4e73b46f76e371c1ad6f74ec`.

## Construction history (not formal rows)

1. First preflight command stopped before Xvfb because its output directory was already created by the host (`FileExistsError`); zero app/MCP/input operations.
2. A separate preflight using `libreoffice --calc --nologo --nodefault` did not bind a Calc window; the only nontrivial new candidate was an Inkscape child and the other candidate was 1x1 with no identity. Retained as `STOP_PREFLIGHT`; no MCP or input.
3. Replacing only the construction launch argv with the repository fixture's `libreoffice --calc` produced three visible distinct owner-bound windows, 0 input/model/network operations, and a removed X socket. The first cleanup predicate counted zombie `/proc` entries as live; a separate corrected predicate treated zombies as non-running and confirmed no remaining live owned PID.
4. On the final pinned image, `preflight.py` and `runner.py` compiled in Docker; `construction-05` again passed the 3/3 identity and neutral cleanup gate. No formal MCP calls were consumed.

Formal output path: `formal01/`. Independent audit output path: `audit01/`. Preserve every formal output and its first disposition; do not rerun this allocation to repair publication or audit defects.