# Issue #4083 — exact crop partial recompute calibration

## H/T/D/C/U
H, T, D, C and U are frozen in Issue #4083. This local copy is authoritative only together with the published source hashes.

### Variables
| Symbol | Meaning | SI unit | Definition | Domain | Type |
|---|---|---|---|---|---|
| B | baseline process CPU time per 24-request case | s | process_time_ns / 1e9 | >0 | scalar |
| C | candidate process CPU time per 24-request case | s | process_time_ns / 1e9 | >0 | scalar |
| R | candidate/baseline CPU ratio | 1 | C/B | >0 | scalar |
| N | requests per case | 1 | fixed 24 | 24 | integer |

Primary cost gate: median R over the three METADATA repetitions <= 0.75. Dimension check: seconds/seconds is dimensionless.

Correctness is prior to cost: all 216 baseline/candidate outputs must match exactly and all authority flags remain false. Timing cannot rescue a semantic mismatch.
