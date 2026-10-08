# A02 construction record

Before formal freeze, `test_construction.py` exercised the candidate data builder and raw-auditor function in process; it did not invoke either CLI or create formal raw output.

- First construction test command: six tests; five passed, one failed because the auditor did not yet bind every case to its declared state stratum. This defect was confined to construction.
- Construction repair added exact case-state expectations and strict independent record checks.
- Second command: six tests passed.
- Third command: eight tests passed, including corrupt effects, interval-state mutation, transport capture/delivery collapse, mandatory-cue omission, false stop outcome, false decision, and visible-cost mutation.
- Final pre-freeze construction suite: 8/8 passed. `py_compile` and `git diff --check` passed.
- Candidate CLI invocations before freeze: 0. Auditor CLI invocations before freeze: 0. Formal retries before freeze: 0.

Construction failures are preserved here and do not count as formal candidate/auditor outcomes. The final source hashes and current-main base are bound in `FREEZE.json`.
