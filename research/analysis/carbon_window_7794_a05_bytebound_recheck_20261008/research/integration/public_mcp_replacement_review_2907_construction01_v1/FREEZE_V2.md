# Construction 02 — root replacement boundary, corrected response projection

Allocation: `public-mcp-replacement-review-2907-docker-20260927-construction02`.
Predecessor construction01 remains immutable as `STOP_CALLER_RECEIPT_SHAPE`; its first MCP call returned a nested receipt and no Chromium replacement was attempted. This is a distinct fresh container, X server, three app processes, MCP process/session and `construction02/` output directory. Only the caller receipt projection is corrected. No outcomes are pooled and no replay/continuation is permitted.

## H/T/D/C/U

- **H:** After the original Chromium window is closed and replaced with an unrelated root window from a different process and XID, the persistent public MCP server's original configured `family_roots[chromium]` prevents `interface_inspect_target` from minting a review ID. It should fail closed, preserve old target/revision and emit no input.
- **T:** One local Docker Linux/amd64 run with one Inkscape, Calc and Chromium; one persistent stdio MCP session; observe all three, close original Chromium, prove old window and launcher exit, launch a new Chromium under a distinct profile/process/XID, focus it, call inspect only, and explicitly do not dispatch after a failed/incomplete review. Close session; preserve all request/response/receipt/images.
- **D:** Scoped boundary PASS iff process PID, owner PID and XID differ; old window/launcher are gone; inspect returns `needs_review`, has no review ID, and reports `outside configured transient family`; server target and binding revision remain original/1; dispatch count is zero; close is clean; MCP server exits; no model/network calls. Identity uncertainty is STOP; an inspect/review success is HOLD pending safety verification.
- **C:** Same pinned Docker image as construction01; `--pull=never --network none`, source read-only, isolated `:143` Xvfb/Openbox, fresh Chromium profiles. The only harness correction is a public nested-receipt projection. Current main code identity will be reported using the relevant Git blob hashes; inherited source closure is not called an exact full-main snapshot.
- **U:** Not full #2907 mixed-app four-transition integration, an API for safe root replacement, authenticated window identity, caller freshness, independent task effect, #2789 acceptance, model/product quality or runtime promotion.

No workflow was dispatched. Formal allocation remains unclaimed.

