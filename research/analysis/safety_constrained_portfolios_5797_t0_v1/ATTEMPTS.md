# Construction attempts and retained first outputs

These are synthetic T0 construction/debugging events, not candidate/live allocation retries. They remain in order for provenance.

## Attempt 1 — invalid negative control

Original candidate put `release` in the capability labels. It selected `cheap_a + rare_sentinel` for cost 5; therefore the intended coverage-only omission was not present. The test failed. Output and test status are retained in `attempt1.raw.json` and `attempt1_test.raw.txt`. The matrix was then changed before the audited construction was run.

## Independent oracle attempt 1

The separate auditor raised `TypeError` when unioning an empty subset. Exact first output is in `audit_attempt1.raw.txt`. The auditor implementation alone was corrected to use an empty-set identity.

## Independent oracle attempt 2

The auditor raised `AssertionError` because a test assertion incorrectly required every same-cost subset to detect release loss. Exact first output is in `audit_attempt2.raw.txt`. The assertion was corrected to the planned negative-control direction.

## Final synthetic T0 execution

The candidate and independent oracle each enumerated 8 portfolios; 4 candidate tests passed. Their independently emitted conditions and outputs are retained in `candidate.raw.json` and `audit.raw.txt`. The host environment is Python 3.12.10; Docker daemon was unavailable, so this did not run in a container.
