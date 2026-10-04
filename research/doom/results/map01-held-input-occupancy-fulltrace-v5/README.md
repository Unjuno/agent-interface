# MAP01 held-input occupancy full-trace v5

This posthoc reconstruction fixes a completed-hold boundary defect: an earlier verified empty-input release caps occupancy even when the program later completes normally. Captures at or after that release cannot certify held occupancy. The original v4 sources and outputs remain unchanged.

## H/T/D/C/U

- H: Full-trace event reconstruction; key occupancy is interval-censored between acknowledgement/capture evidence and verified empty release.
- T: Deterministic synthetic regression with an early verified release at 40 ms, in-loop captures at 30 and 80 ms, and final capture at 90 ms. Compare candidate reconstruction to the independently implemented raw auditor v6.
- D: PASS only when both derive confirmed-through 30 ms, release-by 40 ms, lower bound 18 ms, and upper bound 30 ms; observations at/after release must not extend confirmation.
- C: If there is no earlier verified empty release, retain the prior completed-hold final-snapshot bound. Existing frozen v38/v39 raw evidence remains immutable and was not a new experiment.
- U: Synthetic regression verifies the newly reported edge case; applicability to retained data depends on trace event availability. Prior reports contain no completed-row early verified input release, so no historical totals should be silently rewritten.

## Unit/reference table

| Symbol | Meaning | Unit | Range/assumption | Type |
|---|---|---|---|---|
| t_ack | First acknowledged key-down | ns | Trace monotonic timestamp | Integer |
| t_confirm | Latest in-loop capture strictly before earliest verified release | ns | t_ack <= t_confirm < t_release when available | Integer |
| t_release | Earliest verified empty-input timestamp | ns | Verified release evidence only | Integer |
| L | Confirmed occupancy lower bound, t_confirm - t_ack | ms | Nonnegative | Float |
| U | Occupancy upper bound, t_release - t_admit | ms | Admission precedes release | Float |

## Retained v38/v39 posthoc reanalysis

Using the frozen raw traces from main commit `4ca1db66b6adcb4ea15fc3c744315ad39a87749e`, the v5 candidate was run once on each retained run and the independent v6 raw auditor was run once over both outputs. Raw inputs and original v4 candidate outputs were read-only.

| Trace | Holds | Lower–upper total | Independent raw audit | v4 rows/intersections/totals |
|---|---:|---:|---|---|
| v38 | 11 | 3,048.890–4,039.878 ms | PASS, 0 errors | Exact match |
| v39 | 29 | 6,301.200–8,452.733 ms | PASS, 0 errors | Exact match |

The early verified empty-input cap does not change any retained hold row, decision intersection, or total. In v39, the existing single partial-admission/cancel-ack race remains one row with a zero positive lower bound. Full commands, frozen input hashes, and output hashes are in [POSTHOC_REANALYSIS.md](POSTHOC_REANALYSIS.md).

