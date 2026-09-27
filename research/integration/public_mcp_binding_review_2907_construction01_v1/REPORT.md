# Issue #2907 — public MCP modal target review / stale binding construction

## Result

Local Docker construction01: `PASS_CONSTRUCTION_BINDING_REVIEW_SCOPED`.

One Calc process launched its native `Open` dialog with Ctrl+O. Through one persistent stdio MCP server session, `interface_inspect_target` identified a distinct focused transient window (title `Open`, window ID `6294546`, family root `6292261`). `interface_review_target` rechecked and bound that window, changing the server-owned `binding_revision` from 1 to 2. A dispatch whose caller revision was 1 while the owner was at 2 returned core `STALE_BINDING` with `backend_emissions=0`. A second dispatch with revision 2 sent only Escape plus the required release; it completed, emitted two backend operations, and verified empty keys/buttons. The same session closed with a verified final release, and the per-call request/report receipts were retained.

The explicit inspection/review steps are read-only and grant no authority. The local fixture supplied a lease-shaped contract field as required by the runtime schema; that is not a lease minted or validated by the public MCP server. No model or network calls occurred. This is construction evidence, not a full formal allocation.

## H/T/D/C/U

- **H:** The public persistent-X11 MCP owner can bind an explicitly reviewed focused Calc modal, advance its own binding revision, refuse an old-revision dispatch before emissions, and admit a bounded neutral Escape/release at the new revision.
- **T:** One fresh local Docker X11 display, one Calc window and native Open dialog, one stdio client/server session; inspect → review → stale revision control → fresh Escape/release → close. Raw MCP responses, images and server request/report files are retained in `construction01/`.
- **D:** Pass only for distinct modal identity, owner revision 1→2, core `STALE_BINDING`/0 emissions, fresh completion/verified neutral release, consistent session identity and independent offline raw audit. All these gates passed. One initial independent-auditor attempt failed due to the auditor reading the session ID from the wrong trace field; the auditor was corrected without modifying raw evidence. The first Docker audit setup also stopped before audit because a read-only image filesystem rejected an unnecessary mkdir; it made no changes to experiment evidence. The successful audit ran in a separate network-disabled, read-only Docker container and returned `PASS_RAW_AUDIT`, errors=[] for request order `observe, inspect_target, review_target, dispatch, dispatch, close`.
- **C:** Docker image `public-mcp-three-app-2907:formal01`, ID `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`, Linux/amd64; network disabled; source mounted read-only; isolated `:142` Xvfb/Openbox and one Calc process. The seven source Git blob IDs below were independently matched against GitHub main at `609787159651da728b6a9158ed1ec052c77a897a`.
- **U:** Does not prove caller-issued observation sequence freshness (MCP explicitly documents it as a caller assertion), authenticated window identity, the full four-transition mixed-app schedule, app-effect oracle agreement, #2789 six-task acceptance, task/model/product quality, general reliability, or runtime promotion. No source/runtime code was changed by this experiment.

## GitHub-main source identity

The run's environment JSON inherited the source label `c193b77ddf84bb77fbaa480307c4b23600feedb1`; that is **not** asserted as the current main SHA. For this experiment's relevant code, local Git blob hashes matched GitHub main `609787159651da728b6a9158ed1ec052c77a897a`:

| Main path | Git blob |
|---|---|
| `runtime/cli_v1/mcp_server.py` | `82a7841b53a0618ecbf74b4ead8157a42b62112e` |
| `runtime/cli_v1/mcp_session.py` | `b27dbc6c19d0a2df2b77c81a140cdc16b02d2509` |
| `runtime/cli_v1/api.py` | `6318f0d2fe0b0533d694175e2521eb86946dbed1` |
| `runtime/cli_v1/observe.py` | `08460ae506afcd0f9ad89b91064d121c55c5b419` |
| `runtime/cli_v1/x11_target_review.py` | `3804964e9b7f3a933f0cf060b7552efc09073403` |
| `runtime/backends/x11_v1/session.py` | `e973b2f3f827951634344a320cd833a80a899d9e` |
| `runtime/core_v1/contract.py` | `87154518107e4231a6f8ec06e976d2856b375d1d` |

This seven-file comparison is the source-identity claim; the inherited 94-file closure is not represented as a byte-for-byte snapshot of that main commit.

## Evidence map

- `FREEZE.md`: pre-run H/T/D/C/U and gates.
- `runner.py`: one-use construction driver.
- `auditor.py`: independent offline raw-evidence checker.
- `construction01/result.json`, `construction01/mcp/`, `construction01/server-receipts/`: raw response, image, request and report evidence.
- Docker first audit setup STOP and corrected auditor FAIL are retained in this report; no formal rerun occurred.

GitHub Actions/workflows were not used or dispatched. This is only a bounded construction PASS for Issue #2907; keep #2907 and #2789 open.

