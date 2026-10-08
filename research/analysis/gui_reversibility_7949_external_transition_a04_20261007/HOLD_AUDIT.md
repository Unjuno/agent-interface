# A04 formal outcome: HOLD_AUDIT

The frozen candidate was invoked once and exited 0. The frozen auditor was invoked once and exited 1 before writing `audit.json`.

The candidate output classifies the baseline as `UNIVERSALLY_UNIFORM`, the old revision-1 certificate after the revision-2 external transition as `UNKNOWN_STALE_CERTIFICATE`, the refreshed certificate as `UNIVERSALLY_UNIFORM` with final state `010`, and the sequence-gap case as `UNKNOWN_EVENT_CHAIN`. Candidate stdout is preserved but is not an accepted scientific result because the independent audit did not complete.

Auditor failure:

```text
AssertionError: ['journal_gap raw history does not reconcile']
```

The auditor's raw-history validation treated the expected gapped journal as an audit error instead of recognizing the candidate's fail-closed `UNKNOWN_EVENT_CHAIN` classification as the preregistered expected disposition. This is an auditor implementation/expectation mismatch. No auditor retry, source patch, candidate rerun, or post-freeze replacement is allowed in A04.

- Classification: `HOLD_AUDIT`
- Candidate invocations: 1, exit 0
- Auditor invocations: 1, exit 1
- Retries: 0
- `candidate.raw.json`: 687 bytes, SHA-256 `1018b4c87545ee90e6f4087b6a94c6651a936e0bec49e6ffd6e64653589f16ed`
- `candidate.stderr.txt`: 0 bytes, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- Auditor traceback is retained in the execution-tool record; auditor stdout did not produce a result file.

This finite experiment supports no PASS/FAIL scientific conclusion. A future successor must fix and independently pretest the auditor before a new freeze.
