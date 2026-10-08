# Issue #3212 PID-reuse audit gap — 2026-09-20

Additive adversarial contract test. No live PASS record is changed.

## H/T/D/C/U

- H: The independent display/generation audit must reject a positive effect that reuses the old generation's Chromium PID/window identity without proving a new process start epoch or generation transition.
- T: Retrieved the current `audit.py` and corrected live raw JSONL from main. In a Docker invocation, changed only the positive p2 row's correlated `cdp_browser.pid`, `chromium_pid`, and X11 window PID to the old PID `10`, retained display/profile/XID, set `launch_epoch_ns=3`, and marked it `ADVERSARIAL_SAME_PID`.
- D: The current audit returned `PASS_AUDIT rows=3 controls=3 errors=0` for the adversarial same-PID positive row, even though no evidence linked PID `10` to a new process start epoch or a new generation. The live same-display experiment separately observed real PID transitions `10→134/130/133`; this adversarial row is a contract test, not a browser effect claim.
- C: `FAIL_AUDIT_PID_REUSE_NOT_DETECTED`. The audit correlates current PID/display/profile but does not compare old versus new process start epoch/generation. Do not treat its PASS on this adversarial input as safety evidence.
- U: Extend the audit schema with old/new process start times, generation, launch epoch ordering, and receipt lineage; require strict inequality/new identity for positive p2 before rerunning the live acceptance audit.

## Raw result

```text
input: positive_p2_effect with old PID=10, launch_epoch_ns=3, same display/profile/XID
current audit: PASS_AUDIT rows=3 controls=3 errors=0
formal disposition: FAIL_AUDIT_PID_REUSE_NOT_DETECTED
```
