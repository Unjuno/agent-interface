# Explicit X11 activation integration

The existing input-focus operation could focus Inkscape while Calc still covered
the screen. An explicit optional activation operation now requests activation
from an EWMH window manager. It records active-client/focus confirmation without
claiming visible readiness or task completion. See
[operation semantics](../../backends/x11_v1/ACTIVATION.md).

| Trial | Saved Calc cells | Saved SVG x | Outcome |
| --- | --- | --- | --- |
| two-app-primary-01 | 150,625 (goal 150,626) | 50 (goal 56) | Focus-only switch remained visually on Calc; primary stopped |
| explicit-window-activation-primary-01 | 134,317 | 56 | Files correct with recovery; driver failed on mistyped close tool |
| explicit-window-activation-primary-02 | 108,161 | 56 | Staged editing, verified explicit close, runner exit 0 |

The primary agent viewed returned images before deciding the next action. The
last trial used one persistent public MCP session, 15 calls and 14 images.
After each activation it reviewed the image and selected the editing region in
a separate dispatch. Independent workbook/SVG scoring ran after primary review
and explicit close. All trials used private Linux/Xvfb/Openbox fixtures.

The failed candidate trial's driver received `Unknown tool: interface_close_session`,
then crashed while assuming JSON. Its files were recovered from the retained
fixture after cleanup, not through the normal scoring path. The second driver
lists available tools, checks tool names and preserves non-JSON error replies.
The correct tool is `interface_close`. The failed trial has no verified explicit
close receipt and must not be counted as a clean success.

The baseline and candidates use different seeds; candidate02 also changes the
editing policy. This is integration evidence, not a controlled causal performance
comparison. Application readiness, repaint delay, real model tokens/cost, useful
feedback latency and human-tempo performance remain unproven. A window-manager
confirmation duration alone measures none of these. This does not complete the
broader mixed-application acceptance task.

`raw.tar.gz` retains requests, responses, images, source snapshots, outcomes and
local check02 (200 protocol / 90 harness tests). `manifest.json` hashes every
archive member. Source snapshots distinguish the pre-commit working trees used
by the trials. Original failure records are preserved. Run
`python runtime/results/explicit-window-activation-01/verify.py` with openpyxl
installed to verify hashes, workbook/SVG values, image forwarding, session
continuity and close evidence. The verifier does not independently judge pixels.
