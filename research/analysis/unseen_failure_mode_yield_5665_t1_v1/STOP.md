# T1 attempt 01 — source-hash preflight STOP

- Allocation: `issue5665-failure-mode-yield-t1-20261001-01`
- Disposition: `STOP_SOURCE_HASH_PREFLIGHT`
- Runner invocations: 0; auditor invocations: 0; raw artifact created: false.
- Cause: the frozen auditor SHA-256 was transcribed incorrectly, so the
  pre-run gate stopped before invoking the candidate.
- The original machine-readable STOP is preserved unchanged in
  [`results/t1-host-01/STOP.json`](results/t1-host-01/STOP.json).

This is a pre-execution stop, not a scientific failure or PASS. The corrected
allocation -02 is an independent successor with its own result. No command was
rerun and no historical outcome was changed for this recovery.
