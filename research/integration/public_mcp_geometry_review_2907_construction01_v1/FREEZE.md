# Construction01 — public MCP same-window geometry revalidation

Date: 2026-09-27. Allocation: `public-mcp-geometry-review-2907-docker-20260927-construction01`.

## H/T/D/C/U

- **H:** In a persistent public MCP session, a visible same-XID Calc geometry change can be inspected and explicitly reviewed; review advances server binding revision; an old program revision is refused before input; a fresh revision can perform only neutral Escape/release.
- **T:** One fresh Docker Linux/amd64 Xvfb/Openbox, one Calc process/window, one persistent stdio MCP session. Observe initial Calc, measure geometry with independent X11 tools, resize that same XID to a smaller visible size, independently remeasure, inspect/review focused target, send stale-revision negative control, send fresh Escape/release, verify same XID and resized geometry, close. Retain raw MCP and server receipts. No document edits or save operations.
- **D:** Scoped pass requires same native XID and launcher/owner identity, independently measured geometry changed, inspection evidence identifies same XID and new dimensions, review advances revision 1→2, stale dispatch returns core `STALE_BINDING` with zero backend emissions, fresh revision dispatch completes neutral, and close/final release verifies empty keys/buttons. Any uncertainty is HOLD/STOP; one invocation, no retry.
- **C:** Docker image `public-mcp-three-app-2907:formal01` (`sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`), `--pull=never --network none`, source read-only, one fresh `:144` display. The public API session and seven relevant MCP/runtime Git blobs previously verified against current main `4cd309f690df29f6e24567ec957929de3dd68221`.
- **U:** Caller observation sequence remains asserted rather than server-issued; X11 window metadata is not authenticated; no Chromium root replacement, full #2907 four-transition schedule, independent app-task effect oracle, #2789 six-task acceptance, model/product/reliability claim, or runtime promotion.

No Actions/workflow dispatch. This is construction evidence only.

## Construction01 HOLD and additive successor02

Construction01 remains immutable as `HOLD_GEOMETRY_UNCHANGED_FOCUS_DIALOG`: Calc stayed 1600×981 despite the requested resize, focus was on `Tip of the Day: 1/225`, review did not bind the main window, and later dispatches were safely refused at the MCP owner gate with no input. Its initial auditor FAIL (exact-title expectation) is preserved. Successor02 is a fresh container/session/output with setup controls to close the tip dialog, unmaximize the main root, independently verify resized geometry, and stop before dispatch unless inspect/review binds the main XID. See `FREEZE_V2.md`; no results are pooled.
