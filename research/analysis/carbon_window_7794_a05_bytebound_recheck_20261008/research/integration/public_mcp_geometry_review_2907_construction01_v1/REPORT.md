# Issue #2907 — same-window geometry review construction

## Disposition

`HOLD_FORMAL_ALLOCATION_AND_EFFECT_ORACLE`. Three non-formal local Docker constructions are retained. Construction03 establishes a scoped geometry/review/stale-binding mechanism, but not the independent application-effect oracle or mixed-app #2907 acceptance.

### construction01

Calc main root XID `6292261` started at 1600×981. An `xdotool windowsize` request exited 0 but the independent geometry check stayed 1600×981. Persistent MCP inspection selected the focused Calc transient `Tip of the Day: 1/225`, not the main root; `interface_review_target` returned `needs_review` and did not advance revision. Two attempted dispatches were both rejected at the MCP owner layer as `SESSION_BINDING_REVISION_MISMATCH`, with `input_dispatched=false`; there was no backend input. Session close was clean and did not need release.

The raw trace is `construction01/trace.json`. Auditor v1 expected the title to equal `Tip of the Day` exactly and failed because the observed title included `: 1/225`. Auditor v2 then incorrectly treated the allowed initial observe as a forbidden call. Both failures are preserved. Separate read-only auditor v3 accepts the observed title prefix and permits initial observe while still requiring no input dispatch; it returned `errors=[]` and confirms this remains a setup HOLD.

### construction02

A fresh container/session attempted to close the tip window with `xdotool windowclose` before geometry setup. The configured Calc XID then failed the initial read-only observation with `BadDrawable`; independent geometry was unavailable, no inspect/review/dispatch followed, and the session closed without release. The trace records `HOLD_GEOMETRY_NOT_CHANGED_STOP_BEFORE_DISPATCH`. The wrapper later raised `KeyError('stale_dispatch')` while trying to format this early stop, so its top-level result is `STOP_CONSTRUCTION_EXCEPTION_NO_RETRY`; both raw trace and wrapper error are preserved. The auditor v2 also expected zero calls and initially rejected this allowed observe-only call; auditor v3 permits the observe and confirms no dispatch occurred.

Neither run changed document content. `construction01` and `construction02` are distinct runs; outcomes are not pooled. No formal allocation occurred.

### construction03 — scoped mechanism result, formal HOLD

A fresh Docker session dismissed Calc's Tip of the Day using Escape, preserved root XID `6292261`, and independently measured the same root changing from 1600×981 at (0,38) to 1280×760 at (81,100). Public MCP inspect selected that root and returned `needs_review`; review selected the same XID and advanced binding revision 1→2. The old-revision dispatch was refused by core as `STALE_BINDING` with zero backend emissions. The current-revision neutral ESC program completed with two emissions and a verified release reporting empty key/button state. Close was clean and independently verified neutral.

The read-only auditor v4 ran in a separate networkless, read-only Docker container and reported `errors=[]`, `scoped_mechanism=PASS`, and `decision=HOLD_FORMAL_ALLOCATION_AND_EFFECT_ORACLE`. It also exposed a runner reporting defect: top-level result says `PASS_GEOMETRY_REVIEW_STALE_BINDING_SCOPED`, while its trace decision remains `HOLD_INCOMPLETE`. Both raw values are retained; therefore the formal disposition stays HOLD. The screen observation confirms capture metadata but there is no independent application-effect oracle, and this is only one Calc root—not the mixed-app #2907 four-transition controller acceptance. No contents-changing input was sent.

## H/T/D/C/U for the intended next rung

- **H:** With the Calc transient tip dismissed in-dialog, geometry changes on the original root remain inspectable/reviewable; review advances its binding and a prior binding is refused before backend input.
- **T:** construction03 executed the above on one persistent public MCP session and a pinned Docker image. A separate read-only networkless Docker auditor checked raw receipts, identity, geometry, dispatch, neutral release, and close.
- **D:** Scoped mechanism PASS: same XID through geometry change, revision 1→2, stale core refusal/0 emissions, fresh ESC/release neutral. Overall formal HOLD: runner top-level/trace decision mismatch and no independent application-effect oracle; the #2907 mixed-app acceptance is untested here.
- **C:** Pinned Docker image `public-mcp-three-app-2907:formal01`, no network, fresh Xvfb/Openbox, one Calc process, source read-only, one new session/output path; no source/runtime code change.
- **U:** Still not server-issued sequence freshness, authenticated native identity, full #2907 four-transition mixed-app integration, independent app-effect oracle, #2789 acceptance, model/product readiness or runtime promotion.

No GitHub Actions/workflows were dispatched. Keep #2907 and #2789 open.

## Source identity

The repository main commit at audit time was `ebc9157e2c3101c073a0405c90432927078c6f15`. GitHub MCP's main tree and the seven relevant blobs were checked directly; each matched the pinned runtime source SHA used by this experiment: `runtime/cli_v1/mcp_server.py` `82a7841b53a0618ecbf74b4ead8157a42b62112e`, `runtime/cli_v1/mcp_session.py` `b27dbc6c19d0a2df2b77c81a140cdc16b02d2509`, `runtime/cli_v1/api.py` `6318f0d2fe0b0533d694175e2521eb86946dbed1`, `runtime/cli_v1/observe.py` `08460ae506afcd0f9ad89b91064d121c55c5b419`, `runtime/cli_v1/x11_target_review.py` `3804964e9b7f3a933f0cf060b7552efc09073403`, `runtime/backends/x11_v1/session.py` `e973b2f3f827951634344a320cd833a80a899d9e`, and `runtime/core_v1/contract.py` `87154518107e4231a6f8ec06e976d2856b375d1d`. The inherited 94-file source closure is not represented as an exact copy of this commit.
