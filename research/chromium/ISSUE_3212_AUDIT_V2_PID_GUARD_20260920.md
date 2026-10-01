# Issue #3212 audit v2 PID/generation guard — 2026-09-20

Additive successor audit; the original audit and its PID-reuse gap remain unchanged.

## H/T/D/C/U

- H: Requiring both generation and process-start ordering prevents an old-PID/XID/display row from being promoted to a positive effect.
- T: A successor `audit_v2.py` was run in `mixed-formal-2992-debian:20260920` with two JSONL controls: a valid new generation (`generation 1→2`, process start `100→200`) and an adversarial same-generation/PID reuse row (`1→1`, `100→100`).
- D: Valid input: `PASS_AUDIT_V2 rows=3 controls=3 errors=0`. Adversarial input: `HOLD_AUDIT_V2 rows=3 controls=3 errors=1`, `ERROR positive_p2_effect: generation/start ordering`.
- C: `PASS_AUDIT_V2_PID_REUSE_GUARD_SCOPED`. The v2 contract rejects the previously exposed audit gap. Values `100/200` are contract-test fixtures, not measured process clocks; the live runner must emit real start epochs before acceptance.
- U: Integrate v2 fields into the live runner and repeat using real `/proc`/CDP launch epochs and retained raw manifests.

## Raw results

```text
valid:       PASS_AUDIT_V2 rows=3 controls=3 errors=0
adversarial: HOLD_AUDIT_V2 rows=3 controls=3 errors=1
```
