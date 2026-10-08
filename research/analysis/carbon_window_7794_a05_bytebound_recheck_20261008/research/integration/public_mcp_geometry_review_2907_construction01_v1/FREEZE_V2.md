# Construction02 — explicit Calc root focus and unmaximize before geometry perturbation

Allocation `public-mcp-geometry-review-2907-docker-20260927-construction02` is a fresh Docker container, fresh display, Calc app, MCP server/session and output directory. Construction01 remains immutable HOLD; its unchanged geometry and focused Tip-of-the-Day dialog are retained. This successor corrects setup control and adds a stop gate before input; it does not pool or overwrite predecessor results.

## H/T/D/C/U

- **H:** With the Calc transient tip dialog closed and main root explicitly focused/unmaximized, an independently verified geometry change on the same XID can be reviewed through persistent MCP, advance binding revision 1→2, refuse old binding with core `STALE_BINDING`/0 emissions, and admit only neutral ESC/release using revision 2.
- **T:** One fresh local Docker Linux/amd64 display; launch one Calc, close only the visible “Tip of the Day” dialog if present, focus the configured main XID, observe at initial geometry, remove Openbox maximized state, move/resize and independently verify width+height changed, observe again, focus main root, inspect/review it, then stale control and safe fresh ESC/release only if review succeeds. Close and retain all raw receipts. If geometry did not change or review did not bind the main XID, stop before dispatch.
- **D:** Pass requires exact same root XID across captures/inspection/review, independent before/after geometry change agreeing with inspect evidence, revision 1→2, stale core refusal/zero emissions, fresh completed ESC with verified neutral release and clean close. Any setup or identity gap is HOLD/STOP; one execution, no retry.
- **C:** Pinned local image `public-mcp-three-app-2907:formal01`, no network/pull, source read-only, fresh `:145` Xvfb/Openbox, one Calc only. Public MCP receipt projection matches the existing public nested schema. Local main-relevant source blobs match the verified current-main hashes; full inherited source closure is not claimed as an exact main snapshot.
- **U:** Does not prove server-issued observation freshness, native identity authentication, full #2907 schedule or task-effect oracle, Chromium replacement, #2789 six-task gate, model/product reliability, or runtime promotion.

No Actions/workflow. Construction only.
