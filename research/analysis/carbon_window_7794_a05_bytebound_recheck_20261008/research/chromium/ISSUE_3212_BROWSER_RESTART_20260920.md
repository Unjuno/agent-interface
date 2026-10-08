# Issue #3212 browser-restart invalidation — 2026-09-20

Additive lifecycle experiment; prior records remain unchanged.

## H/T/D/C/U

- H: A receipt bound to a live Chromium resource must be invalidated when the owning browser process exits; replay after restart must not dispatch input or create an application effect.
- T: Three fresh Docker `--network none` allocations of `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, Xlib/XTEST, and CDP DOM oracle. Each allocation produced valid effects, launched a separate fresh control, then terminated the original browser process and attempted to reuse the original receipt.
- D: `browser_restart` was `admitted=false` in 3/3 with reason `process_exit_resource_invalid`; dispatch was `PROCESS_EXITED_NO_DISPATCH` and no DOM effect occurred. Valid effects and source-lineage rejection also passed in all three allocations; negative session/resource/duplicate cases remained denied; no `BadMatch` occurred.
- C: `PASS_CHROMIUM_BROWSER_RESTART_INVALIDATION_FAIL_CLOSED_SCOPED`. This covers process exit of the declared Chromium resource only; it does not cover graceful browser restart with state restoration, orchestrator restart, timeout, or cancellation.
- U: Add explicit timeout/cancel/orchestrator-restart transitions and verify their terminal cleanup and no-dispatch behavior.

## Raw summary

```json
{"runs":3,"browser_restart_admitted":"0/3","browser_restart_dispatch":"0/3","browser_restart_dom_effect":"0/3","valid_effect":"3/3","negative_cases_denied":"3/3","badmatch_runs":0,"formal_decision":"PASS_CHROMIUM_BROWSER_RESTART_INVALIDATION_FAIL_CLOSED_SCOPED"}
```
