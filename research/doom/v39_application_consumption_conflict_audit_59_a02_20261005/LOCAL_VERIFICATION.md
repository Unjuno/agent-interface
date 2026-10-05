# A02 local verification record

- Frozen input: predecessor PR #7662 head `efb712b1aa6f01d67ed119b266ef479645cfb96a`; A01 raw SHA-256 `3f664d52a492ad9d0cbbbdb70880ffe16a4909d4bf2c2880d51891d523652363`.
- Focused test: `python -m unittest -v research.doom.v39_application_consumption_conflict_audit_59_a02_20261005.test_audit_a02` — PASS, 1 test.
- Syntax: `python -m py_compile .../audit_a02.py .../verify_a02.py .../test_audit_a02.py` — PASS.
- Frozen audit invocation: exit 0, `PASS_RAW_CHRONOLOGY_MUTATION_REJECTED`; untouched baseline/candidate each derive to 15 ordered / 85 incomplete rows. The balanced mutation preserved those counts while producing two classification mismatches per implementation (four total).
- Independent raw verifier: exit 0, `PASS_INDEPENDENT_RAW_AUDIT`, zero errors, four mismatches independently recomputed.
- Broader local check: `python -m unittest discover -s research/doom -p 'test*.py'` — 239 tests, 3 failures and 55 errors. The captured output is `formal/doom-suite.stdout`. Errors include missing sparse-checkout modules (`action_validity_admission_v1`, `input_transition_owner_v4`, `policy_invalidation_guard_v1`, `observable_signal_guard_v2`, `input_owner_v10`), unavailable `vizdoom`, absent retained trace files, and Windows-incompatible pipe operations. Failures include two stale frozen source/workflow hashes and one source-composition expectation mismatch. These are unrelated paths in the broad suite; the A02-focused test passes on the exact same checkout.
- Scope: deterministic retained-JSON audit only. No live game, X server, GUI, model, native input, or application-effect run.
