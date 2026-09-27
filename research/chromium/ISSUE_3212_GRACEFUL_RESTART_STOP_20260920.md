# Issue #3212 graceful browser restart — 2026-09-20

Additive failure/stop record. Earlier process-exit invalidation PASS remains unchanged.

## H/T/D/C/U

- H: After the receipt-owning Chromium process exits, a graceful recovery path should allocate a new browser resource/generation and admit only a newly bound receipt.
- T: Docker `--network none`, `mixed-formal-2992-debian:20260920`, Xvfb, real Chromium, and the existing ready-gated runner. The experiment terminated p1, then attempted to start p2 with a new profile and port before issuing a new receipt/effect.
- D: The p2 launch/ready loop timed out in runs 1 and 2 after the p1 process exit. Run 3 remained in the same launch wait and was stopped at the bounded observation limit. No new-generation DOM effect or graceful-restart PASS was observed. The old process-exit invalidation path remains separately measured as fail-closed.
- C: `STOP_GRACEFUL_RESTART_ALLOCATION_TIMEOUT`. This is an infrastructure/runner failure, not evidence that graceful restart is safe or unsafe. No PASS claim is made.
- U: Preserve the pre-stop logs, diagnose why a second Chromium allocation cannot be discovered after p1 termination, then execute a new successor allocation rather than retrying this exact run blindly.

## Raw disposition

```json
{"attempts":3,"p2_ready":0,"p2_effect":0,"run1":"chromium_window_timeout","run2":"chromium_window_timeout","run3":"stopped_at_bounded_observation_limit","formal_decision":"STOP_GRACEFUL_RESTART_ALLOCATION_TIMEOUT"}
```
