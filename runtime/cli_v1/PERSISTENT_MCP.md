# Optional owned X11 session for public MCP

## Explicit input recovery

After a release cannot be verified, normal dispatch remains blocked. On the same
open persistent-X11 connection, explicitly call
`interface_recover_input(current_binding_revision=...)` to attempt release and
readback of tracked inputs. This never opens/reopens a session or replays the
failed program. No-recovery-needed, stale-revision and unopened-session requests
refuse without release; busy calls use the existing no-queue boundary.

Only verified empty release clears the input block. Failure keeps it sticky.
Success advances binding_revision and invalidates pending target reviews, so old
programs and repeated requests with the old revision cannot silently continue.
Observe and review current application state, then explicitly author a new
program using the returned revision. Recovery establishes input state only:
prior task effects remain unknown, and no visual freshness or lease is issued.
One-shot and guarded modes do not expose this tool. The local X11 session API
also provides `recover_input()`; its caller owns serialization and subsequent
application-state review. MCP retains each request/result before presenting it;
historical `interface_results` reads never repeat recovery.

## Session behavior

Experimental opt-in: add `--session-mode persistent-x11` to `python -m runtime.cli_v1.mcp_server --targets targets.json --output-directory runs --display :N`. The default remains `one-shot`. Configured target names and their original transient-family roots are retained for the entire server lifetime. No observation sequence, lease or input authority is minted. The session tracks its explicit target-registration revision; it is not visual freshness authority.

The first persisted observe/dispatch request opens one X11 connection. Later calls use the existing shared observe_in_session/dispatch_in_session APIs on that connection. Calls are serialized; busy refuses instead of queuing. Request persistence still precedes invocation and report persistence precedes image presentation. Session ID/state are included in persistent requests, reports and responses. Initialization failure is sticky; no automatic reconnect. The session's input-recovery requirement is preserved across calls, including read-only observations. There is no new recovery/reset command.

`interface_close()` is available only in this mode. It refuses busy, retains cleanup evidence and closes the connection without reopening it. After an attempted dispatch it attempts release before closing; a release or close failure remains cleanup_failed. Closing an observation-only connection sends no release/input. Repeated close returns the recorded outcome without repeating native cleanup. Retained results remain readable after close. Normal transport shutdown waits for committed workers, then closes and writes session-ID-close.json. An abrupt process kill/power loss cannot guarantee this shutdown receipt or cleanup. A persistence failure must not be treated as proof that input did not happen.

This option is X11-only. It does not establish cross-platform persistent-session support, cross-process recovery, live freshness authority, task correctness or speedup. Public targets/source assertions retain their current trust limits. Native research visual guards are not automatically added to public dispatch by holding a connection.

Construction tests cover connection reuse, preserved recovery across observation, request-persistence failure before opening, no reopen after failed initialization, close/release failure, busy close and cancellation with a committed worker. A private real-X11/stdio construction verified two observations on one session, explicit close, refusal after close and retained-result reads. The first primary-operated input/save trial failed at modal focus; the explicit review route below subsequently completed a new Calc task. Neither trial establishes a speedup.

## Explicit modal target review (experimental)

The first primary-operated public-MCP Calc trial entered both values but failed to save: focusing the original main window while its format modal was active failed verification. A follow-up private X11 diagnostic confirmed a separate managed modal, not a child-focus false negative. Do not relax focus verification or treat a fresh image as implicit target selection.

In persistent mode, `interface_inspect_target(target)` reports the currently focused managed client, only when its WM_TRANSIENT_FOR ancestry reaches that configured target's original window. It does not focus, register or send input. The response contains title, geometry, native ID, focus/transient ancestry and a one-use 30-second review ID. Only the latest inspection is retained. This is WM metadata, not authenticated identity or an atomic image/focus snapshot.

After reviewing that evidence and the visible surface, explicitly call `interface_review_target(target, window_id, review_id)`. It re-reads and compares the evidence, consumes the review ID, replaces that target's native window and increments the session binding revision. No input is sent, no lease is issued, and an input-recovery requirement remains sticky. Capture and review the newly selected surface before new input. Dispatch must supply the session's current binding revision (initially 1); old revisions refuse before dispatch. Observation sequences and lease assertions still come from the caller. New dialogs require a new inspection and explicit review; returning to the original window uses the same process. One-shot mode has neither tool and retains its existing contract.

Limits: focused-client selection does not enumerate other modal candidates, allow unrelated windows or establish semantic modal identity. The WM relationship and native window IDs do not prevent ID reuse, prove application authenticity, freeze the desktop or protect a later dispatch from changes after review. There is no automatic focus, dismissal, redispatch, source refresh or input recovery. A new primary-operated Calc trial (seed 991304, source eb539b185) completed through this route: 597/624 independently read from saved XLSX, two completed input dispatches with verified release, explicit return to the main window and verified release/close. The earlier failed save (seed 991302) remains retained. These are two different seeded tasks, not a controlled latency comparison.

An optional `screen_region=[x,y,width,height]` argument to `interface_inspect_target` bundles one fresh screen capture with focused-client evidence. It rechecks the same metadata after capture; capture failure or disagreement retains the diagnostic observation without a review ID. No target is selected by inspection. The review lifetime starts after this work completes; the 30-second policy is unchanged. The captured report and image use the existing public observation/presentation path, and `interface_results` rereads them without recapture. Matching metadata before/after does not make the screenshot atomic, prove redraw, or grant input authority.
