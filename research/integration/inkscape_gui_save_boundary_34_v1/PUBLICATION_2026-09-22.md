# Retrospective publication note — 2026-09-22

This directory publishes the previously completed conversation-local allocation
`inkscape-gui-save-boundary-34-20260922-01` under Issue #34.

This is **not** GitHub preregistration and is **not** a new formal experiment.
The original local freeze, construction failures, scientific result, and the
historically true `STOP_GITHUB_WRITE_CAPABILITY_UNAVAILABLE` records remain
unchanged. This continuation only delivers retained evidence now that GitHub
write actions are available.

## H / T / D / C / U

**H.** Current canvas state, verified input neutrality, and saved-document state
are distinct postconditions. A current saved SVG verdict must not be promoted to
current canvas truth, and matching canvas pixels must not be promoted to saved
document completion.

**T.** Six fixed action/save/Undo schedules x two repetitions = 12 fresh
Inkscape 1.4 GUI sessions, split before execution into four immutable three-case
batches. Input was real XTEST keyboard/pointer input in fresh authenticated
private Xvfb sessions. The originating allocation was locally source-frozen
before formal input; formal reruns/replacements/post-freeze source edits were 0.

**D.** Retained decision:
`PASS_GUI_CANVAS_SAVE_BOUNDARY_SCOPED`. Independent raw audit reconciles 12/12
cases with errors=[]; 13/13 semantic corruption controls reject; 16/16
construction/audit tests pass. Two MOVE_NO_SAVE cases have the requested canvas
state but not the requested saved SVG. Four later-unsaved move/Undo cases have
the requested saved SVG but no longer the requested current canvas state. All
task endpoints were key/button neutral before teardown.

**C.** This tests ordinary Save/Undo state separation under one declared
Inkscape fixture. The intentionally unsaved controls are not an Inkscape defect.
GUI processes were deliberately SIGTERM-cleaned after final observations, so
their expected exit is -15 rather than fabricated normal exit 0.

**U.** This is research XTEST input, not the public Agent Interface
CLI/API/MCP/core admission/lease path. No model, token/latency, arbitrary-app,
Docker/OrbStack image-attested, cross-platform, autosave/crash-durability,
concurrent-edit, or product claim follows.

Source-freeze SHA-256:
`9c70c6b8e8ee82b02839109134e96f248014aaf4643e1ebc34b5ab3f1eb8d942`.

Originating conversation ZIP:
`agent-interface-inkscape-gui-save-20260922.zip`,
17,495,298 bytes, SHA-256
`431273998006a4a9fc193cdd489425d73157f545530af7618b3ba47b3033bfd8`.

Publication intake main: `95a9f139ea7061475c4fefed88942c7b8ada3d66`.

No shared runtime, workflow, root direction document, predecessor evidence, or
other worker branch is changed by this publication. #34/#57/#2789 and the global
ROADMAP remain open.
