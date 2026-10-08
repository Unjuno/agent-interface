# Construction03 — dismiss transient dialog without destroying Calc root

Allocation `public-mcp-geometry-review-2907-docker-20260927-construction03`. Constructions01 and 02, their raw outcomes and audit attempts remain immutable. This third invocation is a distinct Docker container, Calc instance, X display, MCP server/session and `construction03/` output; it tests a materially different setup action (Escape to dismiss only the transient Tip dialog) and adds explicit pre-dispatch gates. No predecessor result is pooled.

## H/T/D/C/U

- **H:** Sending Escape to the visible Calc “Tip of the Day” dialog, then activating/unmaximizing the original Calc root, will preserve its XID and enable an independently verified same-XID geometry perturbation. The public MCP inspect/review can then bind the focused root and support stale-binding refusal before a fresh neutral Escape/release.
- **T:** Fresh pinned local Docker image, network none. Launch Calc and bind its owned main root. If a visible Tip of the Day dialog exists, activate it and send Escape; verify dialog disappearance and main root remains queryable. Focus and observe root. Remove Openbox maximized state, move/resize, verify actual width and height changed; otherwise close and stop before MCP input. Observe again, focus root, inspect/review the same XID. Only after explicit review advances revision 1→2 run core stale binding control (expect zero backend emissions) and neutral ESC/release with revision 2. Retain all MCP/X11 receipts.
- **D:** Scoped PASS requires transient dialog gone without root loss; geometry changed independently on the same XID; inspect/review evidence matches that root and updated geometry; revision 1→2; old binding returns `STALE_BINDING`/0 emissions; fresh ESC completes with verified empty state; clean close. Any mismatch stops before dispatch and remains STOP/HOLD. Single invocation, no retry.
- **C:** `public-mcp-three-app-2907:formal01`, fixed sha256 `b2b42660e35475baf5ef7a546a8c6901c39f04f69266cd9eebfe49c7ed49ea09`, no pull/network, read-only source, fresh `:146` Xvfb/Openbox, one Calc main window. Relevant runtime source hashes are compared with current main in the final report.
- **U:** No server-issued observation freshness, native identity authentication, full #2907 schedule/task effect, #2789 acceptance, model/product/reliability claim, or runtime promotion.

No workflow dispatch; construction only.
