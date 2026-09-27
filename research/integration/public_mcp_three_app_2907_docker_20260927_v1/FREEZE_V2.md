# Public persistent MCP: three-app observation and close — successor allocation 02

Allocation: `public-mcp-three-app-observe-close-2907-docker-20260927-02`  
Parent: open Issue #2907; integration convergence context: open Issue #2789  
Predecessor: allocation 01 consumed once and retained as `STOP_CALLER_RECEIPT_SHAPE`; its source, raw output, and audits are immutable.  
Status: preregistration; no formal02 MCP call has occurred.  
Execution policy: local Docker Desktop only; no GitHub Actions/workflow.

## H/T/D/C/U

- **H — hypothesis:** Using the public MCP server's documented `agent-interface/review-v1` response and nested `agent-interface/receipt-view-v1` raw report, an additive caller projection can preserve receipt/session identity and permit the same persistent stdio session to observe three distinct owner-bound apps, explicitly close neutrally, and read all retained outcomes.
- **T — treatment:** One fresh `linux/amd64` container from the exact previously frozen derived image, private Xvfb/Openbox, one each of Inkscape → LibreOffice Calc → Chromium. Require new visible owner-bound windows as in FREEZE.md. Start one stdio client/server with `--session-mode persistent-x11`; call observe once per app in fixed order, explicit close once, then read all four results. The only treatment change from allocation01 is the new, separately frozen caller/auditor projection. Use one new session and output path `formal02/`; no replay, continuation, input, dispatch, model, external service, or retry. Run a separate read-only, offline raw audit after collection.
- **D — decision:** `PASS_PUBLIC_MCP_THREE_APP_OBSERVE_CLOSE_SCOPED` only if three distinct owner-bound targets, same session across all observations/close, three returned PNGs and explicit no-input/no-authority flags, neutral close (`release_attempted=false`), all four retained result reads with no operation invocation, complete owned-process/X-socket cleanup, and independent raw auditor PASS with every frozen corruption control rejected. Caller/schema mismatch before the full sequence is `STOP_CALLER_RECEIPT_SHAPE`; missing/inconsistent evidence is HOLD/FAIL by the frozen gate. No retry or relabel.
- **C — controls:** Base main `c193b77ddf84bb77fbaa480307c4b23600feedb1`; same 94-file runtime source closure reconstructed from `51c04e1208014406b7422c5291c97e7023ba68f4`, whose five relevant latest-main Git blobs match exactly; same source tree digest, base/derived image IDs, dependency lock, target identity gate, display, observation region `[0,0,128,96]`, call order, and v1 runner/auditor bytes. The response-normalization wrapper and schema unit tests are new immutable inputs. No outcomes from allocation01 are pooled.
- **U — limits:** Setup/target/observation/close transport only; not full #2907 controller integration, guarded input, app-effect scoring, #2789 six-task acceptance, model integration, benefit/reliability/product evidence.

## Immutable predecessor disposition

Allocation01 was invoked once. Inkscape observation returned with a receipt and session identity, but the runner stopped because its expected status field did not match the public nested receipt layout. Its own result label is preserved verbatim; interpreted status is `STOP_CALLER_RECEIPT_SHAPE`, not an integrated protocol FAIL. The first raw audit's HOLD is retained; additive offline v2 stop-audit independently passed for the one returned row and confirms the sequence was incomplete. Formal01 and both audit outputs remain unchanged. Allocation02 is a new fresh container/session, not a retry or continuation of 01.

## Frozen source and environment identities

- Base: `mixed-app-2499-xauth:v4`, repo digest `sha256:eaf46582f96fd46a1ad6a240928b4c2a828de3d058a4b1490bbadf708d5a52d3`.
- Derived image: `public-mcp-three-app-2907:formal01`, image ID `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`, linux/amd64.
- Runtime source tree SHA-256: `cf93b6cbefcd9fda5e02c82335cd9189e3ac31f303ed1b38253bcac1258a1b5d`. Five relevant main blobs: MCP server `82a7841b53a0618ecbf74b4ead8157a42b62112e`; MCP session `b27dbc6c19d0a2df2b77c81a140cdc16b02d2509`; X11 backend `965443ae5b0f92eab62adfb4aaa00b8963f34679`; X11 session `e973b2f3f827951634344a320cd833a80a899d9e`; core contract `87154518107e4231a6f8ec06e976d2856b375d1d`.
- Frozen inherited runner: `runner.py` SHA-256 `47668fdd02600c1e13c7f43387f05b5ef3c71490be9b6f41e37ea8a986b08d75`; inherited auditor `auditor.py` `57165a818e9f36231f135051af3f2191007f9219e1ca072e26fb0bba9869efc1`.
- New caller adapter `runner_v2.py` SHA-256 `db5ae75fc1f80b62b194cb166715ee540b8251c6a700a6395d7d29d28bf53a4f`; new raw-audit projection `auditor_v2.py` `5c35aeff7eb750aabd3da6a6f6aa34900dd4fb26220b1e36e01a57d345da8518`; schema tests `test_receipt_projection.py` `5ce0442e5ed8fd6f54f7056ea957e84563dcff954320deb8920e75f716195d63`.
- Inherited Dockerfile SHA-256 `2630bff415bbfb06f90742c1f1dfb48966b30d2abf0c542fb04488698c3ee89b`; lock SHA-256 `5933e93e0dc95ee7011794f237dc05626c2b054b4e73b46f76e371c1ad6f74ec`.

## Invocation and evidence handling

Formal: local Docker Desktop, `--network none --pids-limit 512 --memory 4g --cpus 4`, read-only source mount, only `formal02/` writable, `SOURCE_COMMIT=c193b77ddf84bb77fbaa480307c4b23600feedb1`, derived image above, `runner_v2.py` exactly once. Retain stdout/stderr, process exit, all MCP request/response/receipt/report/image bytes, target identities, close receipt, result and hashes.

Independent audit: a separate `docker run --network none --read-only` container; raw bundle mounted read-only, unique audit output directory, no model/input/network/dispatch. Verify all four frozen mutation controls reject. Any output-directory collision is a pre-audit setup stop; use a distinct audit path without touching formal bytes.

Construction only (already completed before this freeze): receipt projection unittest passed 3/3 in a no-network Docker container. Earlier construction invocation mistakes (read-only symlink setup, then missing environment binding) are retained as setup history, not formal outcomes. Docker compile of the frozen wrappers passed. These checks did not call MCP.

Formal02 path: `formal02/`; independent audit: `audit02/`. Preserve all first outcomes; no retry, resume or replacement. Publish the full source/raw/audit and this freeze additively to the owned branch, then open a reviewable evidence PR. No runtime promotion or roadmap completion claim.


