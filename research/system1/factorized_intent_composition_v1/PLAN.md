# #4234 factorized intent composition — H/T/D/C/U

H: replacing categorical intent-ID input with three explicit semantic factors, while holding state, training rows and 14→24→24→4 MLP shape fixed, enables transfer to two intent-factor combinations absent from fitting.

T: NumPy shadow evaluation. Six state features; three binary intent factors; six of eight combinations in training; H0=(1,1,0) and H1=(0,0,1) held out entirely. CATEGORICAL_ID uses 8-way one-hot; FACTORIZED_INTENT uses 3 factor bits + five zero pads. Both inputs are 14 scalars. 4096 train bases, 2048 held-out bases, 2048 seen-control bases. One fit per arm; 700 deterministic Adam minibatch steps, batch512, lr0.003; no retry/tuning.

D: PASS_FACTORIZED_INTENT_COMPOSITION_SCOPED iff factorized held-out accuracy>=0.95, exact both held-out intents/base>=0.90, held-out YIELD recall>=0.98, forbidden-effect proposals<=0.01, seen-control accuracy>=0.97, and held-out accuracy advantage over categorical>=0.15; architecture/provenance/audit/leakage gates must pass. Typed FAIL dispositions follow Issue #4234.

C: synthetic factors/teacher are easier than natural Astra intent; categorical OOV is deliberately a memorization control, not the strongest embedding baseline.

U: no natural-language, Astra, GUI/input, authority, task-effect, token/latency, cross-app or production claim.

## Variable table

| symbol/field | meaning | SI unit | definition | domain/assumption | type |
|---|---|---|---|---|---|
| x | caller-visible state | 1 | six normalized state features | each in [0,1] | vector R^6 |
| i | intent factors | 1 | (pursue, aggressive, threat_focus) | {0,1}^3 | binary vector |
| X | delegate input | 1 | state concatenated with 8 intent slots | 14 scalars | vector R^14 |
| y | teacher disposition | 1 | LEFT/RIGHT/HOLD/YIELD id | {0,1,2,3} | categorical scalar |
| N_train | training rows | 1 | 4096 bases ×6 intents | 24576 | integer |
| N_test | held-out rows | 1 | 2048 bases ×2 intents | 4096 | integer |
| a | semantic accuracy | 1 | correct rows / rows | [0,1] | scalar ratio |
| r_y | YIELD recall | 1 | predicted YIELD / teacher-YIELD | [0,1] | scalar ratio |

Dimensional check: all model features, labels and decision metrics are dimensionless. Fit elapsed nanoseconds are diagnostic only and do not enter PASS/FAIL.
