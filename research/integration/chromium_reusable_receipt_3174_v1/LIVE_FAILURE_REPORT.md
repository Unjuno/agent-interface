# Chromium live receipt failure

Issue: #3174.

A fresh network-disabled Docker run used image mixed-formal-2992-debian:20260920, Xvfb :155, real Chromium, and XTEST input. The runner attempted both normal new-window and --app mode.

Observed failure:
- window discovery selected an auxiliary Chromium clipboard window;
- XID was 4194304 for both launch phases, so distinct replacement identity was not established;
- Xlib BadMatch occurred during the focus/input path;
- valid receipt row had no independent effect/title change;
- session-restart, replacement, and duplicate rows were denied by the local receipt policy.

Decision: FAIL_CHROMIUM_LIVE_RECEIPT. This is not an infrastructure-only stop: Chromium did launch, but the declared live receipt/effect boundary failed. The prior HOLD and retained guarded-macro PASS remain unchanged.
