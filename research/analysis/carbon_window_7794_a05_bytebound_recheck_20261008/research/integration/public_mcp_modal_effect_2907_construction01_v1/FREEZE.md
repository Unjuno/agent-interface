# Issue #2907 — public MCP Calc modal effect construction01

Allocation: `public-mcp-modal-effect-2907-docker-20260927-construction01`  
Intake/current-main reference at final preflight: `38720c4e459b503c45eda36fa1fa5f89e551909e`  
Image: `public-mcp-three-app-2907:formal01`, immutable ID `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`, Linux/amd64.  
Execution: local Docker only; one fresh container/session; no workflow or model.

## H/T/D/C/U

- **H:** In one real public persistent-X11 MCP session, a bounded Ctrl+O dispatch to the configured Calc root produces an independently visible Open dialog; explicit target inspection/review can bind that transient surface; an old binding is rejected before backend emissions; a fresh ESC dispatch dismisses the dialog; independent X11 inspection confirms absence and explicit review returns binding to the original Calc root.
- **T:** Start a fresh Xvfb/Openbox and Calc process. Dismiss only the startup Tip dialog with Escape if present and verify the original Calc root XID remains. Through public MCP, observe root (seq 1), dispatch only `CTRL+O` plus `release_all`, then use X11 properties/window enumeration as independent effect oracle. Inspect and review the dialog, observe the reviewed surface (seq 2), test stale revision 1 against current revision 2 with F6, then dispatch ESC at revision 2. Independently verify the dialog disappeared. Inspect/review the original root again, observe it (seq 3), test stale revision 2 against current 3 with F6, then send one fresh ESC/release. Close the same session and make only read-only retained-result calls afterwards. Preserve every caller response, image, server request/report, process/window identity, and final cleanup receipt.
- **D:** Scoped PASS only when both app effects (dialog appeared after MCP Ctrl+O and disappeared after MCP ESC) are independently evidenced; the same root and transient family are identified; binding advances root→dialog→root; both stale controls are rejected with zero backend emissions; fresh dispatches complete with verified neutral release; session/retained ledger and cleanup are consistent. Any gate failure is retained STOP/HOLD/FAIL and no consequential input follows an unmet prerequisite.
- **C:** Current-main relevant runtime blobs individually recorded and compared with the source snapshot; source bind-mounted read-only; `--pull=never --network none --pids-limit 512 --memory 4g --cpus 2`; fresh display `:151`; no user files mounted; only dedicated result mount writable. A separate read-only/network-disabled Docker auditor independently reconstructs the raw call ledger and effect observations. No retries or outcome-driven tuning.
- **U:** One Calc/Open dialog, synthetic local lease-shaped input, no authenticated controller authority, no six-task direct/integrated comparison, no full mixed-app focus/geometry/replacement schedule, no human-tempo or broad reliability claim. It is an effect-oracle construction and not the full #2907 or #2789 acceptance.

No workflow dispatch. No content is opened, saved, or modified; the only fresh actions are Ctrl+O, Escape, and explicit release.

## Source and runner freeze

The mounted source closure is commit `51c04e1208014406b7422c5291c97e7023ba68f4`; it is **not** represented as the exact 38720 main tree. Before freezing, GitHub MCP read the current main tree and confirmed these seven runtime blob IDs are unchanged and match the runtime files in the pinned closure:

| Runtime path | Git blob SHA |
|---|---|
| `runtime/cli_v1/mcp_server.py` | `82a7841b53a0618ecbf74b4ead8157a42b62112e` |
| `runtime/cli_v1/mcp_session.py` | `b27dbc6c19d0a2df2b77c81a140cdc16b02d2509` |
| `runtime/cli_v1/api.py` | `6318f0d2fe0b0533d694175e2521eb86946dbed1` |
| `runtime/cli_v1/observe.py` | `08460ae506afcd0f9ad89b91064d121c55c5b419` |
| `runtime/cli_v1/x11_target_review.py` | `3804964e9b7f3a933f0cf060b7552efc09073403` |
| `runtime/backends/x11_v1/session.py` | `e973b2f3f827951634344a320cd833a80a899d9e` |
| `runtime/core_v1/contract.py` | `87154518107e4231a6f8ec06e976d2856b375d1d` |

Frozen local SHA-256: `runner.py` `b303f930d04f3f488337da609ec2cba2b84f6816b7d9df5f902c19d524ed17d6`; `auditor.py` `b3361cf1e40556f775dd9634783b9098194d057675cc916bb097bf060f61648c`; static preflight v1 `3c77c8349c6f6d27afbcf37fb9709d3b4ab376076f2856ffc63a7e2b4a73d07a`; preflight v2 `6caf7812de0e3156474067c1042399ee23ee5029743caafb6d950f6ac7c54839`. The two historical preflight outcomes above are separate from the frozen action construction. Static preflight v2 passed on the same runner code except for the later metadata/source-identification-only edit; the final hash will be revalidated before this construction executes.

Final frozen-runner preflight v2 was rerun in a fresh `--network none --read-only` Docker container after the metadata edit: py_compile passed; all three public `interface_validate` cases returned `static_valid=true`, `backend_checked=false`, `runtime_admission=not_evaluated`; display opened/input dispatched were both false. Exact output is in `PREFLIGHT_PASS03.json`. `PREFLIGHT_STOP01.md` and `PREFLIGHT_FAIL02.md` preserve earlier container/harness outcomes without pooling them.

The mounted writable output parent is the otherwise-empty local `run-output/`; the runner creates `run-output/construction01/`. The source package remains mounted separately at `/study:ro`.
