# Construction history — before formal freeze

All entries below are nonformal construction checks. Candidate and independent-auditor formal-role invocation counts remained 0 throughout this period.

1. Wrote `test_candidate.py` first and ran `python -B -m unittest -v test_candidate.py`. It failed as expected with `ModuleNotFoundError: candidate`; the candidate module did not yet exist.
2. Added the minimum scorer and ran the same tests. Initial errors showed the scorer assumed richer memory records than the isolated contract tests supplied (`KeyError: relation_family`). Adjusted structured matching to accept either the frozen counterexample key or relation-family key.
3. Re-ran candidate tests: 3/3 passed; `py_compile` passed.
4. Wrote `test_audit.py` before `audit.py` and ran it. It failed as expected with `ModuleNotFoundError: audit`.
5. Added the separate auditor. The first integrated construction suite ran all nine tests but one clean-packet assertion found that the independently authored `valid_v2` labels for unaffected mappings had ignored the changed target envelope. Corrected those oracle labels (not the candidate output); no formal role had run.
6. Re-ran `python -B -m unittest -v test_candidate.py test_audit.py`: 9/9 passed. The five audit mutations each produce a nonempty rejection reason in their direct regression tests.
7. Added hand-derived outcome-rate assertions and re-ran the final construction suite normally and under `python -O`: 9/9 passed in both modes; `py_compile` passed for candidate, auditor, and both test files.

The integrated construction suites were invoked four times in total: one truth-oracle discrepancy run, one passing normal run, and the final normal and optimized runs. Across them `candidate.run` was called 24 times, direct `score_candidate` assertions ran 12 times, and independent `audit_payload` invocations totaled 24. These are construction checks, not formal outputs. The formal candidate has not been run, the formal auditor has not been run, and neither role has been retried. The final pre-freeze validation counts and exact source hashes are in `FREEZE.json` once created.
