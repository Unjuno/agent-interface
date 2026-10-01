# Issue #2975 predeclared UNO offset sweep

Task: `LO-NATURAL-CONTENTION-2975-20260920-01`  
Issue: [#2975](https://github.com/Unjuno/agent-interface/issues/2975)  
Image: `agent-interface-lo2966:20260920@sha256:551f399a59ec7bd238d22c11c5d53ee14a12be6ede6d5184e4320e6cf62a7944`  
Network: `none`  
Runner SHA-256: `76b2c617e51b2225449eb4742c064e0c543ebf8acfd56b804a8063b3710d03cb`

## H / T / D / C / U

- H: a frozen schedule sweep can distinguish a typed natural conflict from the zero-offset case where concurrent callers both commit from an obsolete observation.
- T: run 0, 1, 5, 10, 20, and 50 ms predeclared independent-writer offsets, five fresh rows per offset, without a parent barrier or sleep inside the cooperative mutation boundary. Preserve #2966 and #438.
- D: `PASS_NATURAL_CONFLICT_BOUNDARY_SCOPED` requires no stale accepted effect; the zero-offset stale-commit case is `FAIL_STALE_EFFECT_ACCEPTED`.
- C: one pinned LibreOffice/UNO topology and Draw fixture, 30 natural rows; no race probability, crash atomicity, distributed transaction, or general GUI claim.
- U: offset 0 is a boundary failure for this runner's cooperative check; positive offsets expose explicit conflict rejection. No claim is made about deployment frequency.

## Result

`FAIL_STALE_EFFECT_ACCEPTED` at the 0 ms boundary.

| writer offset | rows | typed outcome pattern | final A/B |
|---:|---:|---|---|
| 0 ms | 5/5 | writer `APPLIED`; controller `APPLIED` | A=1200 or 1700 / B=5000 |
| 1 ms | 5/5 | writer `APPLIED`; controller `CONFLICT_REJECTED` | 1200 / 5000 |
| 5 ms | 5/5 | writer `APPLIED`; controller `CONFLICT_REJECTED` | 1200 / 5000 |
| 10 ms | 5/5 | writer `APPLIED`; controller `CONFLICT_REJECTED` | 1200 / 5000 |
| 20 ms | 5/5 | writer `APPLIED`; controller `CONFLICT_REJECTED` | 1200 / 5000 |
| 50 ms | 5/5 | writer `APPLIED`; controller `CONFLICT_REJECTED` | 1200 / 5000 |

At 0 ms both independent callers observed A=1000 and both returned `APPLIED`; the final value varied by completion order. The controller had no currentness/refusal record, so this is not a successful intended effect under #2975's gate. Positive offsets generated typed rejection, but do not erase the 0 ms failure.

This is a separate successor result. It does not modify or pool #2966 or the forced-interleave #438 rows.

