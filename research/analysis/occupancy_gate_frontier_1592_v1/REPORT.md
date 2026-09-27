# MAP01 occupancy-gate frontier — Issue #1592

## H/T/D/C/U

- H: the retained width/upper gate `(U-L)/U <= q` is exactly equivalent, under nested inward refinement, to `dL + (1-q)dU >= (U-L)-qU`.
- T: Decimal arithmetic with retained `L=6301.200 ms`, `U=8452.733 ms`, `q=0.25`; exact controls plus 200,000 seeded valid nested refinements.
- D: retained aggregate bounds only; no new model, GUI, MAP01 allocation, or runtime call.
- C: analytical planning result; no prediction of realized telemetry, useful control, survival, gameplay, latency, or recovery efficacy.
- U: live telemetry may narrow endpoints non-additively; this frontier does not authorize a new formal allocation.

## Result

| quantity | value |
|---|---:|
| weighted inward deficit | 38.34975 ms |
| pure-lower requirement | 38.34975 ms |
| pure-upper requirement | 51.133 ms |
| random valid refinements | 200,000 |
| candidate/direct mismatches | 0 |

Boundary controls agreed exactly: zero refinement fails, pure lower and pure upper pass, 38.349 ms fails, and 38.350 ms passes. Existing v38/v39 results and thresholds are unchanged.
