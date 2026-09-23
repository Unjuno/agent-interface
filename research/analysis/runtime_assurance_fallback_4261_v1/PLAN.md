# Runtime assurance fallback — H/T/D/C/U

## H
After a frozen monitor invalidates an advanced proposal, a separately verified bounded fallback can preserve |x|<=5 and useful safe progress better than ADVANCED_OR_STOP, without stale advanced retake.

## T
Finite reversible 1-D plant. x is position, u in {-1,0,1}, exogenous drift d in {0,1}. Monitor admits advanced proposal only if |x+u+d|<=4. Verified fallback is u=-sign(x). Construction used a separate eight-scenario development table and is excluded.

Formal data are prospectively frozen and unexecuted before source freeze: 12 held-out grid schedules x0={2,3,4} × onset={0,2} × duration={2,5}; two late-result schedules; one nominal control; one fallback-unavailable control. Each is evaluated under ADVANCED_OR_STOP and RUNTIME_ASSURANCE_FALLBACK = 32 formal policy/scenario rows. Fourteen fallback-available disturbance/late schedules form the efficacy denominator. Fallback-unavailable tests YIELD/release only.

## D
PASS_RUNTIME_ASSURANCE_FALLBACK_SCOPED iff candidate has zero invariant-violating ticks on all 14 eligible held-out schedules, aggregate violations are strictly below ADVANCED_OR_STOP, safe-progress ticks are strictly greater, held_nominal final states match with zero violations, fallback unavailable yields without fallback action, stale retakes=0, all terminal releases true, independent audit/corruption/source integrity pass. No formal rerun/tuning.

## C
The monitor knows current drift in this fixture. A real monitor may have incomplete state. The simple fallback is verified only for this plant/invariant.

## U
No GUI/model/learned-policy quality/tokens/MAP01/product claim. This tests switching semantics only.

## Variables
| symbol | meaning | SI unit | definition | domain | type |
|---|---|---|---|---|---|
| x | plant position | 1 | discrete state | integer | scalar |
| u | controller input | 1/tick | bounded command | {-1,0,1} | scalar |
| d | exogenous drift | 1/tick | frozen disturbance | {0,1} | scalar |
| S | safety bound | 1 | |x|<=S | S=5 | scalar |
| M | advanced monitor margin | 1 | admit iff |x+u+d|<=M | M=4 | scalar |
| N | formal rows | 1 | 16 scenarios × 2 policies | 32 | integer |

Dimension check: x changes by (u+d) per discrete tick; all quantities share the same dimensionless fixture position unit.
