# Formal execution record

Inputs frozen at `2026-10-01T17:56:04Z`, base main `69a1bf509eb432e5e3c0c294d05ad7671d86adb6`; all frozen source SHA-256 values were checked before execution. No retries.

1. `python candidate.py` — exit 0; 8 cases × 3 policies = 24 decision rows; `oracle_fields_read=0`.
2. `python effect_simulator.py` — exit 0; 24 independent effect events. Unauthorized add-ons: PLAIN 5, TARGET_ONLY 5, FRESH_EFFECT_BOUNDARY 1. Three all-policy transition events include one FRESH residual race.
3. `python -m unittest -v test_contract.py` — exit 0; 10/10 tests passed, including source digest mutation, scorer-field separation, pre-admission block, authorized opt-in, and residual-race retention.
4. `python audit.py` — exit 0; `METHOD_PASS_SCOPED_WITH_RESIDUAL_RACE`, 8 cases, 24 decisions/events, zero audit errors. Pre-admission unauthorized effects: TARGET_ONLY 4, FRESH_EFFECT_BOUNDARY 0. FRESH total remains 1 due the post-admission race.

The residual is essential: the final current-effect read/admission is not atomic with the subsequent click. This result does not claim that the fresh gate solves that race.

