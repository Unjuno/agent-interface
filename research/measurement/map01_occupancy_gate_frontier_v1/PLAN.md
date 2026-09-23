# MAP01 occupancy gate frontier v1

Task: MAP01-OCCUPANCY-GATE-FRONTIER-20260918-001 / Issue #1592.

## H
For gate-native integer-microsecond fields W,U and q=a/b with 0<a<b, a valid refinement W'=W-dW, U'=U-dU, U'>0 passes W'/U' <= a/b iff b*dW-a*dU >= b*W-a*U.

## T
Independent frontier and Fraction-based direct checker; fixed boundary controls; exhaustive 1ms grid around retained v38/v39 plus 250,000 seeded valid refinements. Retained v38/v39 values are copied from main #443 result, not recomputed from lower/upper fields.

## D
PASS iff candidate/direct mismatch0, controls pass, v38 zero-refinement PASS, v39 zero-refinement FAIL, v39 deficit=153403us, pure-width minimum=38351us, lower-fixed pure-upper minimum=51135us, formal1/reruns0, independent audit/integrity pass.

## C
This is an exact planning relation for the frozen diagnostic gate, not a physical law or a prediction of realized telemetry.

## U
Rounded gate-native fields only; no inference from independently rounded L/U/W identity, no live/model/GUI evidence.
