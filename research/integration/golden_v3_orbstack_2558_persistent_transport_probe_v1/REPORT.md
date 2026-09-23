# #2558 persistent app-server transport probe

Date: 2026-09-20 (Asia/Tokyo)

## H/T/D/C/U

- H: the existing app-server client can keep one host-local Codex process and one thread alive across multiple turns; this should be the transport seam for the eventual persistent golden route.
- T: launch `codex app-server --stdio` on macOS, initialize, start one ephemeral read-only thread, then issue two sequential `turn/start` requests on that same thread and process.
- D: initialization passed; thread/start passed; first turn completed in 6426ms; second turn completed in 3449ms. Both turns returned completion status. This probe used text-only prompts and did not drive the GUI fixture.
- C: `PASS_PERSISTENT_APP_SERVER_TWO_TURN_TRANSPORT_SCOPED`.
- U: connect this proven persistent transport to the OrbStack fixture's keyboard-contract observation and native handle/effect gates; then run the preregistered six-task cold/reuse/reuse/repair/reuse/reuse route.

## Constraints and warnings

- This is not a #2558 integrated golden success: no GUI allocation, image grounding, native action, visual revalidation, or repair route was included.
- The process emitted existing environment warnings: models-cache schema mismatch (`missing field base_instructions`), MCP Cloudflare auth worker failures, and plugin/skill loader warnings. These did not prevent the two text turns, but must be diagnosed or explicitly gated before the formal run.
- No retry of the same allocation is claimed; the result is a transport probe only.
