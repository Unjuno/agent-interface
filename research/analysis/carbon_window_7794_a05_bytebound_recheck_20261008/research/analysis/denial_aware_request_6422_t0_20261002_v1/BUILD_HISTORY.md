# Construction history

All entries are retained for method transparency; pre-implementation failures are not scientific outcomes.

1. Wrote the behavioral CLI tests first. Initial red run: 5/5 assertions failed because `candidate.py` did not yet exist (subprocess exit 2); no candidate implementation ran.
2. Added the finite candidate. Construction suite: 5/5 passed; the suite invoked the candidate once on the synthetic fixture.
3. Wrote the auditor rejection test before `audit.py`. Red run: expected audit exit 1 but got exit 2 because `audit.py` did not yet exist; no auditor implementation ran.
4. Added an independent standard-library-only auditor. Full construction suite: 6/6 passed. This suite invoked the candidate once and invoked the auditor once against an intentionally empty/malformed raw object; it rejected the missing 14-row corpus as `ROW_COUNT_MISMATCH`.
5. After the source package and hashes were frozen and read back byte-for-byte from the additive Git branch, the formal candidate ran once, exit 0, and the formal raw-only auditor ran once, exit 0. No retry or post-run source repair occurred.

The two construction candidate invocations and one construction negative-audit invocation are separate from the single formal candidate and single formal raw audit. The initial missing-script subprocess attempts are test-construction failures, not executions of candidate/auditor code.
