# Construction 01 — public MCP root-window replacement boundary (STOP retained)

Date: 2026-09-27. Allocation: `public-mcp-replacement-review-2907-docker-20260927-construction01`.

## H/T/D/C/U

- **H:** A persistent public MCP server whose `family_roots[chromium]` is the original Chromium window cannot explicitly inspect/review a Chromium replacement launched as an unrelated root window. It should fail closed, return no review ID, retain the original target/revision, and emit no input.
- **T:** One fresh local Docker Linux/amd64 X11 display; launch Inkscape, Calc and Chromium as separately identified visible processes; initialize one stdio MCP server with persistent-X11; observe each app through that one server session. Close the original Chromium window and its process, launch replacement Chromium with a new user-data directory and prove both PID lineage and native XID differ. Focus replacement and call only `interface_inspect_target(chromium)`; do not dispatch after rejection. Retain raw MCP responses and server request/report receipts, then close the persistent connection.
- **D:** Scoped boundary PASS only if original and replacement Chromium have distinct owned PIDs and XIDs, old process/window are gone, inspection returns no review ID because the replacement is outside the configured transient family, session target and binding revision remain unchanged, no dispatch/input occurs, and neutral close succeeds. If inspect returns evidence/review for the unrelated replacement, HOLD pending rechecking its identity contract. Setup/identity ambiguity is STOP; one invocation, no retry.
- **C:** Local Docker image `public-mcp-three-app-2907:formal01` (`sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`), network none, source read-only, fresh Xvfb/Openbox, isolated Chromium profiles, current public MCP owner API. Public-main relevant source blobs will be compared to the recorded hashes. No GitHub Actions/workflow.
- **U:** This does not prove the full #2907 four-transition controller schedule, a safe replacement-root refresh mechanism, caller observation freshness, authenticated native identity, effect oracle, #2789 six-task gate, model/task quality, or product readiness. A boundary failure is evidence of missing integration, not a claim that no other API can ever refresh a root.

## Construction01 STOP and additive successor02

Construction01 stopped on the first Inkscape observation because the runner expected a top-level `status` instead of the public `agent-interface/review-v1` nested raw receipt. The MCP observation itself returned; no replacement was attempted. Raw request/response/report evidence is retained under `construction01/` and is not rewritten. Successor02 uses a fresh Docker container, fresh applications and MCP session, a distinct output directory, and an additive response projection only. It is not a retry/continuation of the consumed construction01 invocation and no outcomes are pooled. Successor02 gates/results are in `FREEZE_V2.md`.

