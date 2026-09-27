# #4240 seen-intent trainability precondition — H/T/D/C/U

H: holding the #4234 factorized representation, teacher, architecture and optimizer family fixed, changing only Adam steps 700→2800 can establish competence on disjoint states from the same six seen intent combinations.

T: no held-out-composition evaluation. Six allowed intents only; forbidden {(1,1,0),(0,0,1)} must never appear in generated formal rows. 4096 training bases, 2048 validation bases, 6 intents each. FACTORIZED_INTENT only. Same14→24→24→4 MLP, init, batch512, lr0.003. Exactly SHORT700 and LONG2800 one fit each.

D: PASS_SEEN_INTENT_TRAINABILITY_SCOPED iff LONG accuracy>=0.97, exact-all-six/base>=0.90, YIELD recall>=0.98, forbidden-effect rate<=0.01, and accuracy gain over SHORT>=0.10; heldout absent and audit/integrity gates pass. Typed FAILs per Issue #4240.

C: more steps may still be insufficient or overfit. A PASS only clears a precondition for a fresh future transfer test.

U: no unseen-intent metric, Astra/natural language, GUI/input, authority, task-effect, token/latency or product claim.

## Variable table
| symbol | meaning | SI unit | definition | domain | type |
|---|---|---|---|---|---|
| x | state | 1 | six normalized caller-visible features | [0,1]^6 | vector |
| i | allowed intent factors | 1 | six seen combinations only | {0,1}^3 minus two forbidden tuples | binary vector |
| S | optimizer steps | 1 | SHORT=700, LONG=2800 | positive integer | scalar integer |
| a | validation accuracy | 1 | correct/rows | [0,1] | scalar ratio |
| r_y | YIELD recall | 1 | correct YIELD/teacher-YIELD | [0,1] | scalar ratio |

Dimensional check: all scientific variables and gates are dimensionless; diagnostic fit time is not a decision variable.
