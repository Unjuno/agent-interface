# Active-XID / visible-pixel contrast — construction03

Date: 2026-09-28. Parent evidence: `history/construction01-stop/run.json` and `history/construction02/run.json`; construction02's two original screenshots are retained beside its receipt.

## H/T/D/C/U

- **H:** With two fully overlapping application-like windows, direct X input focus can make the requested client the active XID and satisfy the current-main native bridge's `review_window` focus-ancestry gate while leaving the other client visually on top. An explicit EWMH activation should change the topmost stacking entry and the independently sampled public-capture pixel to the requested client.
- **T:** One fresh local Docker Desktop construction, using current main commit `2dadbde96a3774614f0dff8b51f95dbef9d05716`, pinned image `agent-interface-desktop-integration:local-01` (`sha256:44634c6599b9713b382da9937db38d409c9e66bcbce95aaf2bfeae7793c11385`), `--network none`, read-only root/source, private Xvfb/Openbox, and two overlapping colored `xmessage` clients. Capture a baseline, request direct focus on Inkscape, call the production `NativeHandleBridge.review_window`, then EWMH-activate the same window and review/capture once more. No task action, key, pointer, model, or replay.
- **D:** Retain ordered active XIDs, `_NET_CLIENT_LIST_STACKING`, each production bridge review status/revision, exact PNG paths/SHA-256/dimensions/center pixels, source and image identity, process exits, and logs. A separate process audits the retained JSON and PNG bytes.
- **C:** `PASS_FOCUS_PIXEL_SPLIT_SCOPED` only if the first handoff is `reviewed`, active XID is Inkscape while Calc remains topmost and the baseline Calc pixel remains visible; then EWMH activation makes Inkscape both active and topmost and the second bridge PNG shows the authored Inkscape pixel. Image/receipt digests and neutral process cleanup must reconcile. Otherwise preserve FAIL/STOP without retry.
- **U:** Synthetic clients and one Xvfb/Openbox stack only. This tests the production X11 bridge method, not Calc/Inkscape behavior, public MCP transport, task completion, prevalence, or whether activation is the right product default. Existing #2907 real-app task failure remains authoritative.

## Frozen mechanism boundary

The current-main `NativeHandleBridge.review_window` calls `_focus_within_target(window_id)`, switches its target reference, and invokes the public X11 observation path. It does not activate/raise the requested client. The public capture is the complete physical screen, so the independent oracle samples the known overlap center, not metadata/title, to determine which colored client is actually visible there.

Construction02 already observed the first half once; this is a fresh construction with a predeclared positive control. Its STOP receipt remains unchanged.
