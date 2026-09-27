# Construction 01 — persistent MCP target review and stale binding boundary

Date: 2026-09-27. Allocation: `public-mcp-binding-review-2907-docker-20260927-construction01`.

## H/T/D/C/U

- **H:** A real public persistent-X11 MCP server can inspect a freshly focused Calc dialog, explicitly review/rebind that observed window, advance its owner binding revision, refuse a dispatch carrying the prior revision before backend emissions, and then accept a bounded neutral Escape/release program with the new revision.
- **T:** Construction-only local Docker exercise, one Calc process, one stdio MCP client/server, one owned Xvfb/Openbox display, one fixed file-open dialog if the frozen image supports it. Capture inspect/review/dispatch/close responses and every server request/report/receipt. A stale-revision program uses current observation sequence 2, old binding 1, and a harmless F6 key; expected refusal is the MCP owner gate with zero emissions. Fresh action is ESC plus explicit release, then verify completed and empty keys/buttons. No retry; preserve partial evidence.
- **D:** Scoped pass only if a distinct focused modal window ID is observed, review consumes that evidence and advances revision 1→2, stale dispatch is no-input and operation_invoked=false/backend emissions zero, fresh dispatch completes and release is verified empty, and retained records share the server session. If no modal surface is produced, classify modal branch STOP and report exact observed surface; do not relabel same-window review as modal success. If stale gate proceeds into core and returns STALE_BINDING, report that precise distinction; zero-emission control still required.
- **C:** Current public-main MCP source commit to be recorded from GitHub and exact MCP server/session/API/core/X11 dependency Git blobs. Derived image `public-mcp-three-app-2907:formal01` (`sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`), based on frozen `mixed-app-2499-xauth:v4`. Fresh isolated Docker run, network none, mounted source read-only, unique output only. Prior formal observe/close and stale-observation allocations are not pooled.
- **U:** Not an observation freshness proof, native identity attestation, 4-transition mixed-app schedule, task-effect oracle, #2789 six-task acceptance, model/product/reliability evidence, or runtime promotion.

Construction only: one invocation; no GitHub Actions/workflow. Formal decision and independent audit are not claimed by this preregistration.

