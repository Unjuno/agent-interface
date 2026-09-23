# Readiness/focus construction probe (not a formal allocation)

- Image: `issue3419-multiwindow:20260920`, ID `sha256:6274b31351429a9cd2385f76c75c2df9f817c3dca6d285f4cd8ccceb88d8d1ad`.
- Network: none; separate Xvfb container.
- Probe source: `probe_focus.py`, SHA-256 `e701a2ff808a71d84280b242804ebef4ff85572259fb91a1025c0f29fcd0d212`.
- Readiness uses an anchored window-name regex and then exact `getwindowname` equality. It focuses each XID, confirms `getwindowfocus`, and sends Return to the focused window.
- Observed output: p2 XID 2097155 and decoy XID 4194307; for each, focus_rc=0, focused ID matched, send_rc=0, and its own DOM title effect was observed.
- Scope: a construction-only input-delivery check. No allocation rows, stale receipt, or acceptance claim.
