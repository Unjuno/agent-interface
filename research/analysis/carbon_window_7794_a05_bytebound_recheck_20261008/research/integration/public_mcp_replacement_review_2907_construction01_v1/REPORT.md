# Issue #2907 — public MCP Chromium root replacement boundary

## Outcome

`HOLD_OLD_LAUNCHER_LIVENESS_UNVERIFIED` (construction02; no formal allocation).

The fresh Docker run opened Inkscape, Calc and Chromium in one persistent public MCP session and obtained three no-input observations. It then closed the original Chromium window and launched a replacement with a separate profile and process. Replacement window ID, launcher PID and `_NET_WM_PID` were all distinct from the original. The old X window was gone.

When replacement Chromium was focused, `interface_inspect_target(target="chromium")` returned `needs_review` without a `review_id`, with `ValueError('focused client is outside configured transient family')`. The MCP owner's `chromium` target remained the original XID `8388611`, binding revision remained 1, and no dispatch occurred. `interface_close` closed the session with `release_attempted=false`; the MCP server was absent after stdio shutdown.

However, the old Chromium launcher PID was still present after the wait and the runner did not record whether it was a live process or zombie. That gate is unresolved; therefore the raw audit is HOLD, not PASS. The source failure is consistent with the code's fixed `family_roots[target]` constraint, but does not prove no other safe root-refresh route exists.

## Preserved caller STOP and audit history

- **construction01:** STOP_CALLER_RECEIPT_SHAPE on first Inkscape observation. Public MCP returned nested `agent-interface/review-v1`; the runner expected top-level `status`. No replacement action occurred. Raw evidence is retained under `construction01/`.
- **construction02 auditor v1:** FAIL_RAW_AUDIT because it counted the later inspect call as one of the baseline observations. No raw evidence changed.
- **construction02 auditor v2:** independent read-only, network-disabled Docker audit; `errors=[]`, disposition `HOLD_OLD_LAUNCHER_LIVENESS_UNVERIFIED`.

## H/T/D/C/U

- **H:** The persistent MCP review owner, configured with an original Chromium root, cannot mint a review ID for a replacement root outside that original transient family; it should preserve the old binding and fail closed without input.
- **T:** Construction02 used one new Linux/amd64 Docker container, Xvfb/Openbox, three owner-identified apps and one MCP session; three observations, old Chromium window close, fresh-profile Chromium replacement, read-only inspect, and close. Construction01 and its STOP were not replayed or pooled.
- **D:** Distinct old/new XID and launcher/owner PIDs, old window gone, no review ID and explicit transient-family error, unchanged target/revision, zero dispatch, clean no-release close, and MCP server exit were observed. Old launcher process liveness was ambiguous, so the preregistered PASS gate was not met and the report remains HOLD.
- **C:** Image `public-mcp-three-app-2907:formal01`, `sha256:b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`; `--pull=never --network none`; source and independent audit inputs read-only; fresh `:143` display and Chromium profiles. The run metadata identifies the inherited 51c04 source closure without claiming it as an exact full-main snapshot; seven relevant code blob hashes previously matched main `609787159651da728b6a9158ed1ec052c77a897a`.
- **U:** Not the complete #2907 four-transition schedule, safe replacement-root refresh, authenticated identity, observation-sequence freshness, task-effect oracle, #2789 six-task acceptance, model/product readiness or runtime promotion.

## Next research implication

The current public MCP API can rebind a modal child only when X11 transient ancestry reaches the originally configured root. Chromium replacement is a distinct unresolved case. A future integration needs explicit evidence-backed replacement-root generation and safe session target refresh; simply relaxing the transient-family check would be unsafe and is not supported by this experiment.

GitHub Actions/workflows were not dispatched. #2907 and #2789 remain open.

