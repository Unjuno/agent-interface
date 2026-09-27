# MAP01 v6 bound audit successor

Issue #1632. H/T/D/C/U is recorded in the issue and PR.

This additive wrapper executes the unchanged retained v6 audit, then exact-matches all three pair-level coast/recovery no-retained-input upper bounds to the six arm summaries. Any missing, non-integer, or unequal value forces FAIL and `valid_experiment=false`.

The deterministic test preserves the truthful zero-failure case and mutates each of the six bindings independently. Expected result: 6/6 mismatches rejected. This is posthoc synthetic audit evidence only; it does not rerun or authorize the v6 live allocation, and it does not establish recovery efficacy.
