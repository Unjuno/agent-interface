# A02 first outcome

- Candidate invocation: 1, exit 0; four cells, 92 events; stdout digest `37e99f9ac9886c869f6efb0be5f338dc510820a37d8afcb5c65acae8430ce64a`.
- Independent auditor invocation: 1, exit 1. It wrote `audit.json` before failing in its final stdout summary (`NameError: mutations is not defined`).
- The saved audit reports `HOLD_ACCESS_OR_AUDIT`, eight candidate/reconstruction selection/event mismatches, and five frozen mutation controls rejected.
- Read-only diagnosis: candidate labels use `Random.randrange(2)` while the independent oracle uses `Random.getrandbits(1)`; these produce different random streams in this runtime. No formal code was rerun.
- Candidate, auditor, and raw output were not retried. Preserve the JSON audit and exact stderr as the first outcome.
