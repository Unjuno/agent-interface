# Issue #3733 — German XKB XTEST text-delivery experiment

This bundle tests whether the current-main X11 text planner resolves `=` and `*` from a standard German XKB map and whether the resulting real XTEST events decode to `=B2*A2` in a private X11 receiver. It also tests whole-payload fail-closed behavior for a late unsupported Euro character.

The measurement has three fresh German-layout Xvfb servers and one fresh US-layout control, each in a no-network OrbStack container. It sends no input to the host display, a real application, Calc, MCP, or a model. The receiver is `xev`'s private window and its Xlib `XLookupString` event trace.

The backend source is byte-identical to the exact source cited by successor Issue #3733 (`runtime/backends/x11_v1/backend.py`, blob `9cae101a219348077668c8fc086acf8e13154afe`) and is frozen at current main commit `eca4bcc1ee839b80442397e27f238c97d6dd6bb4`. See `PREREG.md` for gates, `CONSTRUCTION-NOTES.md` for the disclosed pre-freeze setup deviation, and `RUNLOG.md` for the formal disposition.

This is a first-rung isolated X11 text-delivery test only. It cannot establish Calc task effects, GUI/API/MCP integration, physical German keyboard behavior, level-3/Compose/IME support, timing benefits, or broad layout correctness.
